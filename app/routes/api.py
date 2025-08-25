"""
API routes for the customer service system
"""

from flask import Blueprint, request, jsonify, session
from app import redis_client, mongo
from app.models.mongo_models import User, Conversation, Message
from app.services.ai_service import HotelAIService
import uuid
import json
from datetime import datetime

api_bp = Blueprint('api', __name__)
ai_service = HotelAIService()

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Docker and load balancers"""
    try:
        # Check database connection
        mongo.db.command('ping')
        
        # Check Redis connection
        redis_client.ping()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': 'ok',
                'redis': 'ok'
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503
    finally:
        pass

@api_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages from web interface"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id') or session.get('session_id')
        user_context = data.get('user_context', {})
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Create or get session
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        # Get or create user
        user_data = mongo.db.users.find_one({'session_id': session_id})
        if not user_data:
            user = User(
                session_id=session_id,
                name=user_context.get('name'),
                email=user_context.get('email'),
                phone=user_context.get('phone'),
                room_number=user_context.get('room_number'),
                guest_type=user_context.get('guest_type', 'guest')
            )
            mongo.db.users.insert_one(user.to_dict())
        else:
            user = User.from_dict(user_data)
            mongo.db.users.update_one(
                {'_id': user._id},
                {'$set': {'last_active': datetime.utcnow()}}
            )
        
        # Get or create conversation
        conversation_data = mongo.db.conversations.find_one({'user_id': user._id, 'status': 'active'})
        
        if not conversation_data:
            conversation = Conversation(
                user_id=user._id,
                channel='web'
            )
            mongo.db.conversations.insert_one(conversation.to_dict())
        else:
            conversation = Conversation.from_dict(conversation_data)
        
        # Save user message
        user_msg = Message(
            conversation_id=conversation._id,
            sender_id=user._id,
            sender_type='user',
            message_text=user_message
        )
        mongo.db.messages.insert_one(user_msg.to_dict())
        
        # Generate AI response
        ai_response = ai_service.generate_response(
            user_message,
            conversation['_id'],
            user_context
        )
        
        # Save AI message
        ai_msg = Message(
            conversation_id=conversation._id,
            sender_id=user._id, # AI messages are also associated with the user's conversation
            sender_type='ai',
            message_text=ai_response['response'],
            intent=ai_response.get('intent'),
            confidence=ai_response.get('confidence'),
            processing_time=ai_response.get('processing_time')
        )
        mongo.db.messages.insert_one(ai_msg.to_dict())
        
        # Update conversation metadata
        mongo.db.conversations.update_one(
            {'_id': conversation._id},
            {
                '$set': {
                    'category': ai_response.get('intent'),
                    'sentiment': ai_response.get('sentiment'),
                    'priority': 'high' if ai_response.get('escalate') else conversation.priority
                }
            }
        )
        
        # Cache conversation in Redis
        redis_client.setex(
            f"conversation:{session_id}",
            3600,  # 1 hour TTL
            json.dumps({
                'conversation_id': str(conversation._id),
                'user_id': str(user._id),
                'last_message': ai_response['response']
            })
        )
        
        return jsonify({
            'response': ai_response['response'],
            'session_id': session_id,
            'conversation_id': str(conversation._id),
            'intent': ai_response.get('intent'),
            'sentiment': ai_response.get('sentiment'),
            'escalate': ai_response.get('escalate', False),
            'suggested_responses': ai_service.get_suggested_responses(ai_response.get('intent', 'inquiry'))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@api_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Get conversation history for admin dashboard"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        channel = request.args.get('channel')
        
        filters = {}
        if status:
            filters['status'] = status
        if channel:
            filters['channel'] = channel
        
        query = {}
        if status:
            query['status'] = status
        if channel:
            query['channel'] = channel

        # MongoDB pagination
        skip_count = (page - 1) * per_page
        conversations_data = mongo.db.conversations.find(query).sort('created_at', -1).skip(skip_count).limit(per_page)
        conversations = [Conversation.from_dict(conv).to_dict() for conv in conversations_data]
        total_count = mongo.db.conversations.count_documents(query)
        
        return jsonify({
            'conversations': conversations,
            'total': total_count,
            'pages': (total_count + per_page - 1) // per_page,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/conversations/<conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """Get messages for a specific conversation"""
    try:
        messages_data = mongo.db.messages.find({'conversation_id': conversation_id}).sort('created_at', 1)
        messages = [Message.from_dict(msg).to_dict() for msg in messages_data]
        
        return jsonify({
            'messages': messages
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """Get analytics data for admin dashboard"""
    try:
        active_conversations = mongo.db.conversations.count_documents({'status': 'active'})
        closed_conversations = mongo.db.conversations.count_documents({'status': 'closed'})
        
        # Message metrics
        today = datetime.utcnow().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        total_messages = mongo.db.messages.count_documents({
            'created_at': {'$gte': start_of_day, '$lt': end_of_day}
        })
        
        avg_response_time_result = Message.collection.aggregate([
            {'$match': {
                'created_at': {'$gte': datetime.combine(today, datetime.min.time()), '$lt': datetime.combine(today, datetime.max.time())},
                'sender_type': 'ai',
                'processing_time': {'$exists': True, '$ne': None}
            }},
            {'$group': {
                '_id': None,
                'avg_time': {'$avg': '$processing_time'}
            }}
        ])
        avg_response_time = list(avg_response_time_result)[0]['avg_time'] if avg_response_time_result else 0
        
        # User metrics
        new_users = User.count_documents({
            'created_at': {'$gte': datetime.combine(today, datetime.min.time()), '$lt': datetime.combine(today, datetime.max.time())}
        })
        
        # Intent distribution
        intent_distribution_result = Message.collection.aggregate([
            {'$match': {
                'created_at': {'$gte': datetime.combine(today, datetime.min.time()), '$lt': datetime.combine(today, datetime.max.time())},
                'sender_type': 'ai',
                'intent': {'$exists': True, '$ne': None}
            }},
            {'$group': {
                '_id': '$intent',
                'count': {'$sum': 1}
            }}
        ])
        intent_distribution = {item['_id']: item['count'] for item in intent_distribution_result}
        
        # Sentiment distribution
        sentiment_distribution_result = Message.collection.aggregate([
            {'$match': {
                'created_at': {'$gte': datetime.combine(today, datetime.min.time()), '$lt': datetime.combine(today, datetime.max.time())},
                'sender_type': 'ai',
                'sentiment': {'$exists': True, '$ne': None}
            }},
            {'$group': {
                '_id': '$sentiment',
                'count': {'$sum': 1}
            }}
        ])
        sentiment_distribution = {item['_id']: item['count'] for item in sentiment_distribution_result}
        
        # Escalation rate
        escalated_conversations = Conversation.count_documents({
            'created_at': {'$gte': datetime.combine(today, datetime.min.time()), '$lt': datetime.combine(today, datetime.max.time())},
            'priority': 'high'
        })
        
        escalation_rate = (escalated_conversations / total_conversations) * 100 if total_conversations > 0 else 0
        
        # Guest Request metrics
        total_guest_requests = Analytics.count_documents({
            'timestamp': {'$gte': datetime.combine(today, datetime.min.time()), '$lt': datetime.combine(today, datetime.max.time())},
            'event_type': 'guest_request_recorded'
        })
        
        # Average conversation length (messages)
        avg_conversation_length_result = Conversation.collection.aggregate([
            {'$match': {
                'created_at': {'$gte': datetime.combine(today, datetime.min.time()), '$lt': datetime.combine(today, datetime.max.time())}
            }},
            {'$project': {
                'message_count': {'$size': '$messages'}
            }},
            {'$group': {
                '_id': None,
                'avg_length': {'$avg': '$message_count'}
            }}
        ])
        avg_conversation_length = list(avg_conversation_length_result)[0]['avg_length'] if avg_conversation_length_result else 0
        
        # Top intents
        top_intents_result = Message.collection.aggregate([
            {'$match': {
                'created_at': {'$gte': datetime.combine(today, datetime.min.time()), '$lt': datetime.combine(today, datetime.max.time())},
                'sender_type': 'ai',
                'intent': {'$exists': True, '$ne': None}
            }},
            {'$group': {
                '_id': '$intent',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ])
        top_intents = {item['_id']: item['count'] for item in top_intents_result}
        
        # Top requested items/services (from analytics)
        top_requests_result = Analytics.collection.aggregate([
            {'$match': {
                'timestamp': {'$gte': datetime.combine(today, datetime.min.time()), '$lt': datetime.combine(today, datetime.max.time())},
                'event_type': 'guest_request_recorded',
                'metadata.request_type': {'$exists': True, '$ne': None}
            }},
            {'$group': {
                '_id': '$metadata.request_type',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ])
        top_requests = {item['_id']: item['count'] for item in top_requests_result}
        
        return jsonify({
            'total_conversations': total_conversations,
            'active_conversations': active_conversations,
            'closed_conversations': closed_conversations,
            'total_messages': total_messages,
            'avg_response_time': round(avg_response_time, 2) if avg_response_time else 0,
            'new_users': new_users,
            'intent_distribution': intent_distribution,
            'sentiment_distribution': sentiment_distribution,
            'escalation_rate': round(escalation_rate, 2),
            'total_guest_requests': total_guest_requests,
            'avg_conversation_length': round(avg_conversation_length, 2) if avg_conversation_length else 0,
            'top_intents': top_intents,
            'top_requests': top_requests
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/conversations/<conversation_id>/escalate', methods=['POST'])
def escalate_conversation(conversation_id):
    """Escalate a conversation to a human agent"""
    try:
        # The 'pass' was likely a placeholder, remove it and indent the rest
        conversation_data = mongo.db.conversations.find_one({'_id': conversation_id})
        if not conversation_data:
            return jsonify({'error': 'Conversation not found'}), 404
        
        mongo.db.conversations.update_one({'_id': conversation_id}, {'$set': {'status': 'escalated'}})
        
        return jsonify({'message': 'Conversation escalated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@api_bp.route('/conversations/<conversation_id>/resolve', methods=['POST'])
def resolve_conversation(conversation_id):
    """Resolve a conversation"""
    try:
        conversation_data = mongo.db.conversations.find_one({'_id': conversation_id})
        if not conversation_data:
            return jsonify({'error': 'Conversation not found'}), 404
        
        mongo.db.conversations.update_one({'_id': conversation_id}, {'$set': {'status': 'closed'}})
        
        return jsonify({'message': 'Conversation resolved successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        conversation_data = mongo.db.conversations.find_one({'_id': conversation_id})
        if not conversation_data:
            return jsonify({'error': 'Conversation not found'}), 404
        
        mongo.db.conversations.delete_one({'_id': conversation_id})
        
        return jsonify({'message': 'Conversation deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/messages/<message_id>', methods=['DELETE'])
def delete_message(message_id):
    """Delete a message"""
    try:
        message_data = mongo.db.messages.find_one({'_id': message_id})
        if not message_data:
            return jsonify({'error': 'Message not found'}), 404
        
        mongo.db.messages.delete_one({'_id': message_id})
        
        return jsonify({'message': 'Message deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile"""
    try:
        user_data = mongo.db.users.find_one({'_id': user_id})
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        user = User.from_dict(user_data)
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users/<user_id>', methods=['PUT'])
def update_user_profile(user_id):
    """Update user profile"""
    try:
        user_data = mongo.db.users.find_one({'_id': user_id})
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        update_fields = {}
        if 'username' in data: update_fields['username'] = data['username']
        if 'email' in data: update_fields['email'] = data['email']
        
        if update_fields:
            mongo.db.users.update_one({'_id': user_id}, {'$set': update_fields})
        
        updated_user_data = mongo.db.users.find_one({'_id': user_id})
        updated_user = User.from_dict(updated_user_data)
        return jsonify(updated_user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    try:
        user_data = mongo.db.users.find_one({'_id': user_id})
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        mongo.db.users.delete_one({'_id': user_id})
        
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/documents/upload', methods=['POST'])
def upload_document_route():
    """Upload a document for processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and document_service.allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            document_id = document_service.upload_document(filename, file_path)
            
            # Asynchronously process the document
            Thread(target=document_service.process_document, args=(document_id,)).start()
            
            return jsonify({
                'message': 'Document uploaded and processing started',
                'document_id': str(document_id)
            }), 202
        except Exception as e:
            current_app.logger.error(f"Error uploading document: {e}")
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'File type not allowed'}), 400

@api_bp.route('/documents/<document_id>', methods=['GET'])
def get_document_route(document_id):
    """Get document details"""
    try:
        document_data = mongo.db.documents.find_one({'_id': document_id})
        if not document_data:
            return jsonify({'error': 'Document not found'}), 404
        
        document = Document.from_dict(document_data)
        return jsonify(document.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/documents/<document_id>', methods=['DELETE'])
def delete_document_route(document_id):
    """Delete a document"""
    try:
        document_data = mongo.db.documents.find_one({'_id': document_id})
        if not document_data:
            return jsonify({'error': 'Document not found'}), 404
        
        # Delete associated chunks first
        mongo.db.document_chunks.delete_many({'document_id': document_id})
        mongo.db.documents.delete_one({'_id': document_id})
        
        return jsonify({'message': 'Document deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
