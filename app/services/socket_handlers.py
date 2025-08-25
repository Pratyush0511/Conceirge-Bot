"""
Socket.IO event handlers for real-time communication
"""

from flask_socketio import emit, join_room, leave_room
from flask import session, request
from app import redis_client
from app.models.mongo_models import User, Conversation, Message
from app.services.ai_service import HotelAIService
import json
import uuid
from datetime import datetime

ai_service = HotelAIService()

def register_socket_handlers(socketio):
    """Register all Socket.IO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        session_id = request.args.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session['session_id'] = session_id
        join_room(session_id)
        
        emit('connected', {
            'session_id': session_id,
            'message': 'Connected to customer service'
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        session_id = session.get('session_id')
        if session_id:
            leave_room(session_id)
    
    @socketio.on('join_conversation')
    def handle_join_conversation(data):
        """Join a specific conversation room"""
        conversation_id = data.get('conversation_id')
        if conversation_id:
            join_room(f"conversation_{conversation_id}")
            emit('joined_conversation', {'conversation_id': conversation_id})
    
    @socketio.on('send_message')
    def handle_message(data):
        """Handle incoming chat messages"""
        try:
            user_message = data.get('message', '').strip()
            session_id = session.get('session_id') or data.get('session_id')
            user_context = data.get('user_context', {})
            message_type = data.get('type', 'text')
            message_metadata = data.get('metadata', {})
            
            if not user_message or not session_id:
                emit('error', {'message': 'Message and session_id are required'})
                return
            
            # Get or create user
            user = mongo.db.users.find_one({'session_id': session_id})
            if not user:
                user_data = {
                    '_id': str(uuid.uuid4()),
                    'session_id': session_id,
                    'name': user_context.get('name'),
                    'email': user_context.get('email'),
                    'phone': user_context.get('phone'),
                    'room_number': user_context.get('room_number'),
                    'guest_type': user_context.get('guest_type', 'guest'),
                    'created_at': datetime.utcnow(),
                    'last_active': datetime.utcnow()
                }
                mongo.db.users.insert_one(user_data)
                user = user_data
            else:
                mongo.db.users.update_one(
                    {'_id': user['_id']},
                    {'$set': {'last_active': datetime.utcnow()}}
                )
            
            # Get or create conversation
            conversation = mongo.db.conversations.find_one(
                {'user_id': user['_id'], 'status': 'active'}
            )
            
            if not conversation:
                conversation_data = {
                    '_id': str(uuid.uuid4()),
                    'user_id': user['_id'],
                    'channel': 'web',
                    'created_at': datetime.utcnow(),
                    'status': 'active'
                }
                mongo.db.conversations.insert_one(conversation_data)
                conversation = conversation_data
            
            # Save user message
            user_msg_data = {
                '_id': str(uuid.uuid4()),
                'conversation_id': conversation['_id'],
                'user_id': user['_id'],
                'message_text': user_message,
                'message_type': message_type,
                'metadata': message_metadata,
                'sender_type': 'user',
                'created_at': datetime.utcnow()
            }
            mongo.db.messages.insert_one(user_msg_data)
            user_msg = user_msg_data
            
            # Emit user message to conversation room
            socketio.emit('new_message', {
                'message': user_msg,
                'conversation_id': conversation['_id']
            }, room=f"conversation_{conversation['_id']}")
            
            # Show typing indicator
            emit('ai_typing', {'typing': True, 'conversation_id': conversation['_id']})
            
            # Generate AI response
            try:
                ai_response = ai_service.generate_response(
                    user_message,
                    conversation['_id'],
                    user_context
                )
            except Exception as e:
                print(f"AI Service Error: {e}")
                # Fallback response
                ai_response = {
                    'response': "Thank you for your message. I'm here to help you with any questions about our hotel services. How can I assist you today?",
                    'intent': 'inquiry',
                    'confidence': 0.5,
                    'sentiment': 'neutral',
                    'processing_time': 0.1,
                    'escalate': False
                }
            
            # Save AI message
            ai_msg_data = {
                '_id': str(uuid.uuid4()),
                'conversation_id': conversation['_id'],
                'message_text': ai_response['response'],
                'sender_type': 'ai',
                'intent': ai_response.get('intent'),
                'confidence': ai_response.get('confidence'),
                'processing_time': ai_response.get('processing_time'),
                'created_at': datetime.utcnow()
            }
            mongo.db.messages.insert_one(ai_msg_data)
            ai_msg = ai_msg_data
            
            # Update conversation metadata
            mongo.db.conversations.update_one(
                {'_id': conversation['_id']},
                {
                    '$set': {
                        'category': ai_response.get('intent'),
                        'sentiment': ai_response.get('sentiment'),
                        'priority': 'high' if ai_response.get('escalate') else conversation.get('priority', 'normal')
                    }
                }
            )
            
            # Cache in Redis
            redis_client.setex(
                f"conversation:{session_id}",
                3600,
                json.dumps({
                    'conversation_id': str(conversation['_id']),
                    'user_id': str(user['_id']),
                    'last_message': ai_response['response']
                })
            )
            
            # Stop typing indicator
            emit('ai_typing', {'typing': False, 'conversation_id': str(conversation['_id'])})
            
            # Emit AI response
            emit('ai_response', {
                'message': ai_msg,
                'conversation_id': str(conversation['_id']),
                'intent': ai_response.get('intent'),
                'sentiment': ai_response.get('sentiment'),
                'escalate': ai_response.get('escalate', False),
                'suggested_responses': ai_service.get_suggested_responses(
                    ai_response.get('intent', 'inquiry')
                )
            })
            
            # Emit to conversation room for admin monitoring
            socketio.emit('new_message', {
                'message': ai_msg,
                'conversation_id': str(conversation['_id'])
            }, room=f"conversation_{conversation['_id']}")
            
            # If escalation is needed, notify admin
            if ai_response.get('escalate'):
                socketio.emit('escalation_needed', {
                    'conversation_id': str(conversation['_id']),
                    'user_id': str(user['_id']),
                    'message': user_message,
                    'intent': ai_response.get('intent'),
                    'sentiment': ai_response.get('sentiment')
                }, room='admin')
            
        except Exception as e:
            # Make sure to stop typing indicator even if there's an error
            try:
                emit('ai_typing', {'typing': False, 'conversation_id': str(conversation['_id']) if conversation else None})
            except:
                pass
            emit('error', {'message': str(e)})
    
    @socketio.on('typing')
    def handle_typing(data):
        """Handle typing indicators"""
        session_id = session.get('session_id')
        conversation_id = data.get('conversation_id')
        
        if conversation_id:
            emit('user_typing', {
                'session_id': session_id,
                'typing': data.get('typing', False)
            }, room=f"conversation_{conversation_id}", include_self=False)
    
    @socketio.on('admin_join')
    def handle_admin_join():
        """Handle admin joining for monitoring"""
        join_room('admin')
        emit('admin_joined', {'message': 'Admin monitoring active'})
    
    @socketio.on('admin_message')
    def handle_admin_message(data):
        """Handle messages from admin to specific conversation"""
        try:
            conversation_id = data.get('conversation_id')
            message = data.get('message')
            agent_id = data.get('agent_id', 'admin')
            
            if not conversation_id or not message:
                emit('error', {'message': 'Conversation ID and message are required'})
                return
            
            # Save admin message
            admin_msg = Message(
                conversation_id=conversation_id,
                sender_type='agent',
                sender_id=agent_id,
                content=message
            )
            db.session.add(admin_msg)
            db.session.commit()
            
            # Emit to conversation participants
            socketio.emit('agent_message', {
                'message': admin_msg.to_dict()
            }, room=f"conversation_{conversation_id}")
            
        except Exception as e:
            emit('error', {'message': str(e)})
    
    @socketio.on('get_conversation_history')
    def handle_get_history(data):
        """Get conversation history"""
        try:
            conversation_id = data.get('conversation_id')
            limit = data.get('limit', 50)
            
            if not conversation_id:
                emit('error', {'message': 'Conversation ID is required'})
                return
            
            messages = Message.query.filter_by(conversation_id=conversation_id)\
                                   .order_by(Message.created_at.asc())\
                                   .limit(limit).all()
            
            emit('conversation_history', {
                'conversation_id': conversation_id,
                'messages': [msg.to_dict() for msg in messages]
            })
            
        except Exception as e:
            emit('error', {'message': str(e)})
