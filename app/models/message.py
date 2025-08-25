"""
Message model for storing conversation messages
"""

from datetime import datetime
import uuid

class Message:
    def __init__(self, conversation_id, sender_type, content, sender_id=None, message_type='text', message_metadata=None, intent=None, confidence=None, processing_time=None, created_at=None, id=None):
        self._id = id if id else str(uuid.uuid4())
        self.conversation_id = conversation_id
        self.sender_type = sender_type
        self.sender_id = sender_id
        self.content = content
        self.message_type = message_type
        self.message_metadata = message_metadata
        self.intent = intent
        self.confidence = confidence
        self.processing_time = processing_time
        self.created_at = created_at if created_at else datetime.utcnow()

    def to_dict(self):
        return {
            '_id': self._id,
            'conversation_id': self.conversation_id,
            'sender_type': self.sender_type,
            'sender_id': self.sender_id,
            'content': self.content,
            'message_type': self.message_type,
            'message_metadata': self.message_metadata,
            'intent': self.intent,
            'confidence': self.confidence,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat()
        }

    @staticmethod
    def from_dict(data):
        return Message(
            id=data.get('_id'),
            conversation_id=data['conversation_id'],
            sender_type=data['sender_type'],
            sender_id=data.get('sender_id'),
            content=data['content'],
            message_type=data.get('message_type'),
            message_metadata=data.get('message_metadata'),
            intent=data.get('intent'),
            confidence=data.get('confidence'),
            processing_time=data.get('processing_time'),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data and isinstance(data['created_at'], str) else data.get('created_at')
        )
