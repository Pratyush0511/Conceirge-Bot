"""
User model for the customer service system
"""

from datetime import datetime
import uuid

class User:
    def __init__(self, session_id, name=None, email=None, phone=None, room_number=None, guest_type='guest', language='en', created_at=None, last_active=None, id=None):
        self._id = id if id else str(uuid.uuid4())
        self.session_id = session_id
        self.name = name
        self.email = email
        self.phone = phone
        self.room_number = room_number
        self.guest_type = guest_type
        self.language = language
        self.created_at = created_at if created_at else datetime.utcnow()
        self.last_active = last_active if last_active else datetime.utcnow()

    def to_dict(self):
        return {
            '_id': self._id,
            'session_id': self.session_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'room_number': self.room_number,
            'guest_type': self.guest_type,
            'language': self.language,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat()
        }

    @staticmethod
    def from_dict(data):
        return User(
            id=data.get('_id'),
            session_id=data['session_id'],
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            room_number=data.get('room_number'),
            guest_type=data.get('guest_type'),
            language=data.get('language'),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data and isinstance(data['created_at'], str) else data.get('created_at'),
            last_active=datetime.fromisoformat(data['last_active']) if 'last_active' in data and isinstance(data['last_active'], str) else data.get('last_active')
        )
