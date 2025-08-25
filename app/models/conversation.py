"""
Conversation model for tracking customer interactions
"""

from datetime import datetime
import uuid

class Conversation:
    def __init__(self, user_id, channel, status='active', priority='normal', category=None, sentiment=None, satisfaction_score=None, agent_id=None, created_at=None, updated_at=None, resolved_at=None, id=None):
        self._id = id if id else str(uuid.uuid4())
        self.user_id = user_id
        self.channel = channel
        self.status = status
        self.priority = priority
        self.category = category
        self.sentiment = sentiment
        self.satisfaction_score = satisfaction_score
        self.agent_id = agent_id
        self.created_at = created_at if created_at else datetime.utcnow()
        self.updated_at = updated_at if updated_at else datetime.utcnow()
        self.resolved_at = resolved_at

    def to_dict(self):
        return {
            '_id': self._id,
            'user_id': self.user_id,
            'channel': self.channel,
            'status': self.status,
            'priority': self.priority,
            'category': self.category,
            'sentiment': self.sentiment,
            'satisfaction_score': self.satisfaction_score,
            'agent_id': self.agent_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

    @staticmethod
    def from_dict(data):
        return Conversation(
            id=data.get('_id'),
            user_id=data['user_id'],
            channel=data['channel'],
            status=data.get('status'),
            priority=data.get('priority'),
            category=data.get('category'),
            sentiment=data.get('sentiment'),
            satisfaction_score=data.get('satisfaction_score'),
            agent_id=data.get('agent_id'),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data and isinstance(data['created_at'], str) else data.get('created_at'),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data and isinstance(data['updated_at'], str) else data.get('updated_at'),
            resolved_at=datetime.fromisoformat(data['resolved_at']) if 'resolved_at' in data and isinstance(data['resolved_at'], str) else data.get('resolved_at')
        )
