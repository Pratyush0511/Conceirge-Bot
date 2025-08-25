"""
Analytics model for tracking system performance and metrics
"""

from datetime import datetime, timedelta
import uuid

class Analytics:
    def __init__(self, metric_type, metric_value, channel=None, date=None, hour=None, analytics_metadata=None, created_at=None, id=None):
        self._id = id if id else str(uuid.uuid4())
        self.metric_type = metric_type
        self.metric_value = metric_value
        self.channel = channel
        self.date = date if date else datetime.utcnow().date()
        self.hour = hour if hour is not None else datetime.utcnow().hour
        self.analytics_metadata = analytics_metadata
        self.created_at = created_at if created_at else datetime.utcnow()

    def to_dict(self):
        return {
            '_id': self._id,
            'metric_type': self.metric_type,
            'metric_value': self.metric_value,
            'channel': self.channel,
            'date': self.date.isoformat(),
            'hour': self.hour,
            'analytics_metadata': self.analytics_metadata,
            'created_at': self.created_at.isoformat()
        }

    @staticmethod
    def from_dict(data):
        return Analytics(
            id=data.get('_id'),
            metric_type=data['metric_type'],
            metric_value=data['metric_value'],
            channel=data.get('channel'),
            date=datetime.fromisoformat(data['date']).date() if 'date' in data and isinstance(data['date'], str) else data.get('date'),
            hour=data.get('hour'),
            analytics_metadata=data.get('analytics_metadata'),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data and isinstance(data['created_at'], str) else data.get('created_at')
        )

    @staticmethod
    def record_metric(metric_type, value, channel=None, metadata=None):
        """
        Create a new analytics record
        Note: In MongoDB implementation, this would be handled by the service layer
        """
        return Analytics(
            metric_type=metric_type,
            metric_value=value,
            channel=channel,
            analytics_metadata=metadata
        )

    @staticmethod
    def get_daily_metrics(metric_type, days=7):
        """
        Get daily metrics
        Note: In MongoDB implementation, this would use aggregation pipelines
        """
        return []

    @staticmethod
    def get_hourly_metrics(metric_type, date=None):
        """
        Get hourly metrics
        Note: In MongoDB implementation, this would use aggregation pipelines
        """
        return []
