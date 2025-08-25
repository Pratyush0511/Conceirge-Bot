"""MongoDB models for the customer service system"""

from datetime import datetime
import uuid
from bson import ObjectId
from app import mongo

class MongoModel:
    """Base class for MongoDB models"""
    collection_name = None
    
    @classmethod
    def find_one(cls, query):
        """Find a single document"""
        return mongo.db[cls.collection_name].find_one(query)
    
    @classmethod
    def find(cls, query=None, sort=None, limit=None):
        """Find multiple documents"""
        query = query or {}
        cursor = mongo.db[cls.collection_name].find(query)
        
        if sort:
            cursor = cursor.sort(sort)
        
        if limit:
            cursor = cursor.limit(limit)
            
        return list(cursor)
    
    @classmethod
    def insert_one(cls, document):
        """Insert a single document"""
        if '_id' not in document:
            document['_id'] = str(uuid.uuid4())
        
        result = mongo.db[cls.collection_name].insert_one(document)
        return document
    
    @classmethod
    def update_one(cls, query, update):
        """Update a single document"""
        return mongo.db[cls.collection_name].update_one(query, update)
    
    @classmethod
    def delete_one(cls, query):
        """Delete a single document"""
        return mongo.db[cls.collection_name].delete_one(query)

class User(MongoModel):
    """User model for MongoDB"""
    collection_name = 'users'
    
    @classmethod
    def create(cls, session_id, name=None, email=None, phone=None, room_number=None, guest_type='guest', language='en'):
        """Create a new user"""
        user = {
            '_id': str(uuid.uuid4()),
            'session_id': session_id,
            'name': name,
            'email': email,
            'phone': phone,
            'room_number': room_number,
            'guest_type': guest_type,
            'language': language,
            'created_at': datetime.utcnow(),
            'last_active': datetime.utcnow()
        }
        
        return cls.insert_one(user)
    
    @classmethod
    def find_by_session_id(cls, session_id):
        """Find user by session ID"""
        return cls.find_one({'session_id': session_id})
    
    @classmethod
    def update_last_active(cls, user_id):
        """Update user's last active timestamp"""
        return cls.update_one(
            {'_id': user_id},
            {'$set': {'last_active': datetime.utcnow()}}
        )
    
    @staticmethod
    def to_dict(user):
        """Convert user document to dictionary"""
        if not user:
            return None
            
        return {
            'id': user['_id'],
            'session_id': user['session_id'],
            'name': user.get('name'),
            'email': user.get('email'),
            'phone': user.get('phone'),
            'room_number': user.get('room_number'),
            'guest_type': user.get('guest_type', 'guest'),
            'language': user.get('language', 'en'),
            'created_at': user.get('created_at').isoformat() if user.get('created_at') else None,
            'last_active': user.get('last_active').isoformat() if user.get('last_active') else None
        }

class Conversation(MongoModel):
    """Conversation model for MongoDB"""
    collection_name = 'conversations'
    
    @classmethod
    def create(cls, user_id, channel='web', status='active', priority='normal', category=None):
        """Create a new conversation"""
        conversation = {
            '_id': str(uuid.uuid4()),
            'user_id': user_id,
            'channel': channel,
            'status': status,
            'priority': priority,
            'category': category,
            'sentiment': None,
            'satisfaction_score': None,
            'agent_id': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'resolved_at': None
        }
        
        return cls.insert_one(conversation)
    
    @classmethod
    def find_active_by_user(cls, user_id):
        """Find active conversation by user ID"""
        return cls.find_one({'user_id': user_id, 'status': 'active'})
    
    @classmethod
    def resolve(cls, conversation_id, satisfaction_score=None):
        """Resolve a conversation"""
        update = {
            '$set': {
                'status': 'resolved',
                'resolved_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        }
        
        if satisfaction_score:
            update['$set']['satisfaction_score'] = satisfaction_score
            
        return cls.update_one({'_id': conversation_id}, update)
    
    @classmethod
    def escalate(cls, conversation_id, agent_id):
        """Escalate a conversation"""
        return cls.update_one(
            {'_id': conversation_id},
            {'$set': {
                'status': 'escalated',
                'agent_id': agent_id,
                'priority': 'high',
                'updated_at': datetime.utcnow()
            }}
        )
    
    @staticmethod
    def to_dict(conversation, include_messages=False):
        """Convert conversation document to dictionary"""
        if not conversation:
            return None
            
        result = {
            'id': conversation['_id'],
            'user_id': conversation['user_id'],
            'channel': conversation['channel'],
            'status': conversation['status'],
            'priority': conversation['priority'],
            'category': conversation.get('category'),
            'sentiment': conversation.get('sentiment'),
            'satisfaction_score': conversation.get('satisfaction_score'),
            'agent_id': conversation.get('agent_id'),
            'created_at': conversation.get('created_at').isoformat() if conversation.get('created_at') else None,
            'updated_at': conversation.get('updated_at').isoformat() if conversation.get('updated_at') else None,
            'resolved_at': conversation.get('resolved_at').isoformat() if conversation.get('resolved_at') else None
        }
        
        if include_messages:
            messages = Message.find({'conversation_id': conversation['_id']}, sort=[('created_at', 1)])
            result['messages'] = [Message.to_dict(msg) for msg in messages]
            result['message_count'] = len(messages)
        
        return result

class Message(MongoModel):
    """Message model for MongoDB"""
    collection_name = 'messages'
    
    @classmethod
    def create_user_message(cls, conversation_id, user_id, content, message_type='text', metadata=None):
        """Create a user message"""
        message = {
            '_id': str(uuid.uuid4()),
            'conversation_id': conversation_id,
            'sender_type': 'user',
            'sender_id': user_id,
            'content': content,
            'message_type': message_type,
            'message_metadata': metadata or {},
            'created_at': datetime.utcnow()
        }
        
        return cls.insert_one(message)
    
    @classmethod
    def create_ai_message(cls, conversation_id, content, intent=None, confidence=None, processing_time=None, metadata=None):
        """Create an AI message"""
        message = {
            '_id': str(uuid.uuid4()),
            'conversation_id': conversation_id,
            'sender_type': 'ai',
            'content': content,
            'message_type': 'text',
            'message_metadata': metadata or {},
            'intent': intent,
            'confidence': confidence,
            'processing_time': processing_time,
            'created_at': datetime.utcnow()
        }
        
        return cls.insert_one(message)
    
    @staticmethod
    def to_dict(message):
        """Convert message document to dictionary"""
        if not message:
            return None
            
        return {
            'id': message['_id'],
            'conversation_id': message['conversation_id'],
            'sender_type': message['sender_type'],
            'sender_id': message.get('sender_id'),
            'content': message['content'],
            'message_type': message.get('message_type', 'text'),
            'metadata': message.get('message_metadata', {}),
            'intent': message.get('intent'),
            'confidence': message.get('confidence'),
            'processing_time': message.get('processing_time'),
            'created_at': message.get('created_at').isoformat() if message.get('created_at') else None
        }

class Document(MongoModel):
    """Document model for MongoDB"""
    collection_name = 'documents'
    
    @classmethod
    def create(cls, filename, file_path, title, description=None, category=None, file_size=None, file_type=None, status='processing'):
        """Create a new document"""
        document = {
            '_id': str(uuid.uuid4()),
            'filename': filename,
            'file_path': file_path,
            'title': title,
            'description': description,
            'category': category,
            'file_size': file_size,
            'file_type': file_type,
            'status': status,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'processed_at': None
        }
        
        return cls.insert_one(document)
    
    @classmethod
    def update_status(cls, document_id, status, processed_at=None):
        """Update document status"""
        update = {
            '$set': {
                'status': status,
                'updated_at': datetime.utcnow()
            }
        }
        
        if processed_at or status == 'processed':
            update['$set']['processed_at'] = processed_at or datetime.utcnow()
            
        return cls.update_one({'_id': document_id}, update)
    
    @staticmethod
    def to_dict(document):
        """Convert document to dictionary"""
        if not document:
            return None
            
        return {
            'id': document['_id'],
            'filename': document['filename'],
            'file_path': document.get('file_path'),
            'title': document.get('title'),
            'description': document.get('description'),
            'category': document.get('category'),
            'file_size': document.get('file_size'),
            'file_type': document.get('file_type'),
            'status': document.get('status', 'processing'),
            'created_at': document.get('created_at').isoformat() if document.get('created_at') else None,
            'updated_at': document.get('updated_at').isoformat() if document.get('updated_at') else None,
            'processed_at': document.get('processed_at').isoformat() if document.get('processed_at') else None
        }

class DocumentChunk(MongoModel):
    """Document chunk model for MongoDB"""
    collection_name = 'document_chunks'
    
    @classmethod
    def create(cls, document_id, text, page_number=None, chunk_index=None, embedding=None):
        """Create a new document chunk"""
        chunk = {
            '_id': str(uuid.uuid4()),
            'document_id': document_id,
            'text': text,
            'page_number': page_number,
            'chunk_index': chunk_index,
            'embedding': embedding,
            'created_at': datetime.utcnow()
        }
        
        return cls.insert_one(chunk)
    
    @classmethod
    def find_by_document(cls, document_id):
        """Find chunks by document ID"""
        return cls.find({'document_id': document_id}, sort=[('chunk_index', 1)])
    
    @classmethod
    def update_embedding(cls, chunk_id, embedding):
        """Update chunk embedding"""
        return cls.update_one(
            {'_id': chunk_id},
            {'$set': {'embedding': embedding}}
        )
    
    @staticmethod
    def to_dict(chunk):
        """Convert chunk to dictionary"""
        if not chunk:
            return None
            
        return {
            'id': chunk['_id'],
            'document_id': chunk['document_id'],
            'text': chunk['text'],
            'page_number': chunk.get('page_number'),
            'chunk_index': chunk.get('chunk_index'),
            'has_embedding': bool(chunk.get('embedding')),
            'created_at': chunk.get('created_at').isoformat() if chunk.get('created_at') else None
        }

class GuestRequest(MongoModel):
    """Guest request model for MongoDB"""
    collection_name = 'guest_requests'
    
    @classmethod
    def create(cls, user_id, request_type, details, status='pending'):
        """Create a new guest request"""
        request = {
            '_id': str(uuid.uuid4()),
            'user_id': user_id,
            'request_type': request_type,
            'details': details,
            'status': status,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'completed_at': None
        }
        
        return cls.insert_one(request)
    
    @classmethod
    def update_status(cls, request_id, status, completed_at=None):
        """Update request status"""
        update = {
            '$set': {
                'status': status,
                'updated_at': datetime.utcnow()
            }
        }
        
        if completed_at or status == 'completed':
            update['$set']['completed_at'] = completed_at or datetime.utcnow()
            
        return cls.update_one({'_id': request_id}, update)
    
    @staticmethod
    def to_dict(request):
        """Convert request to dictionary"""
        if not request:
            return None
            
        return {
            'id': request['_id'],
            'user_id': request['user_id'],
            'request_type': request['request_type'],
            'details': request['details'],
            'status': request.get('status', 'pending'),
            'created_at': request.get('created_at').isoformat() if request.get('created_at') else None,
            'updated_at': request.get('updated_at').isoformat() if request.get('updated_at') else None,
            'completed_at': request.get('completed_at').isoformat() if request.get('completed_at') else None
        }