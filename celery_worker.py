"""
Celery worker configuration for background tasks
"""

from app import create_app, make_celery

app = create_app()
celery = make_celery(app)

@celery.task
def process_analytics():
    """Background task to process analytics data"""
    with app.app_context():
        from app.models.analytics import Analytics
        from app.models.conversation import Conversation
        from app.models.message import Message
        from app import db
        from datetime import datetime, timedelta
        
        # Calculate daily metrics
        today = datetime.utcnow().date()
        
        # Total conversations today
        conv_count = Conversation.query.filter(
            db.func.date(Conversation.created_at) == today
        ).count()
        
        if conv_count > 0:
            Analytics.record_metric('daily_conversations', conv_count)
        
        # Average response time
        avg_response = db.session.query(
            db.func.avg(Message.processing_time)
        ).filter(
            Message.sender_type == 'ai',
            db.func.date(Message.created_at) == today
        ).scalar()
        
        if avg_response:
            Analytics.record_metric('avg_response_time', avg_response)
        
        # Satisfaction scores
        avg_satisfaction = db.session.query(
            db.func.avg(Conversation.satisfaction_score)
        ).filter(
            Conversation.satisfaction_score.isnot(None),
            db.func.date(Conversation.updated_at) == today
        ).scalar()
        
        if avg_satisfaction:
            Analytics.record_metric('avg_satisfaction', avg_satisfaction)

@celery.task
def cleanup_old_sessions():
    """Clean up old Redis sessions"""
    from app import redis_client
    import time
    
    # Get all conversation keys
    keys = redis_client.keys('conversation:*')
    
    for key in keys:
        # Check if key is older than 24 hours
        ttl = redis_client.ttl(key)
        if ttl == -1:  # No expiration set
            redis_client.expire(key, 86400)  # Set 24 hour expiration

@celery.task
def send_escalation_notification(conversation_id, user_id, message):
    """Send notification for escalated conversations"""
    # In production, this would send email/SMS notifications
    print(f"ESCALATION ALERT: Conversation {conversation_id} needs attention")
    print(f"User: {user_id}")
    print(f"Message: {message}")
    
    # Could integrate with email service, Slack, etc.
    return f"Escalation notification sent for conversation {conversation_id}"

if __name__ == '__main__':
    celery.start()
