"""
Admin dashboard routes
"""

from flask import Blueprint, render_template, request, jsonify
from app.models.mongo_models import Conversation, Message, User
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard main page"""
    return render_template('admin/dashboard.html')

@admin_bp.route('/conversations')
def conversations():
    """Conversations management page"""
    return render_template('admin/conversations.html')

@admin_bp.route('/analytics')
def analytics():
    """Analytics page"""
    return render_template('admin/analytics.html')

@admin_bp.route('/api/stats')
def get_stats():
    """Get real-time statistics for dashboard"""
    try:
        # Today's date
        today = datetime.utcnow().date()
        
        # Basic counts
        total_conversations = mongo.db.conversations.count_documents({})
        active_conversations = mongo.db.conversations.count_documents({'status': 'active'})
        total_users = mongo.db.users.count_documents({})
        total_messages = mongo.db.messages.count_documents({})
        
        # Today's metrics
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        today_conversations = mongo.db.conversations.count_documents({
            'created_at': {'$gte': start_of_day, '$lt': end_of_day}
        })
        
        today_resolved = mongo.db.conversations.count_documents({
            'resolved_at': {'$gte': start_of_day, '$lt': end_of_day}
        })
        
        # Average response time (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        avg_response_time_result = mongo.db.messages.aggregate([
            {'$match': {
                'sender_type': 'ai',
                'created_at': {'$gte': yesterday},
                'processing_time': {'$exists': True, '$ne': None}
            }},
            {'$group': {
                '_id': None,
                'avg_time': {'$avg': '$processing_time'}
            }}
        ])
        avg_response_time = list(avg_response_time_result)[0]['avg_time'] if avg_response_time_result else 0
        
        # Satisfaction score (assuming satisfaction_score is now part of Conversation document)
        avg_satisfaction_result = mongo.db.conversations.aggregate([
            {'$match': {
                'satisfaction_score': {'$exists': True, '$ne': None}
            }},
            {'$group': {
                '_id': None,
                'avg_score': {'$avg': '$satisfaction_score'}
            }}
        ])
        avg_satisfaction = list(avg_satisfaction_result)[0]['avg_score'] if avg_satisfaction_result else 0
        
        return jsonify({
            'total_conversations': total_conversations,
            'active_conversations': active_conversations,
            'total_users': total_users,
            'total_messages': total_messages,
            'today_conversations': today_conversations,
            'today_resolved': today_resolved,
            'avg_response_time': round(avg_response_time, 2),
            'avg_satisfaction': round(avg_satisfaction, 1)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/charts/conversations')
def conversation_charts():
    """Get data for conversation charts"""
    try:
        # Last 7 days conversation data
        days = []
        conversation_data = []
        resolved_data = []
        
        for i in range(7):
            date = datetime.utcnow().date() - timedelta(days=i)
            days.append(date.strftime('%Y-%m-%d'))
            
            start_of_day = datetime.combine(date, datetime.min.time())
            end_of_day = datetime.combine(date, datetime.max.time())
            conv_count = mongo.db.conversations.count_documents({
                'created_at': {'$gte': start_of_day, '$lt': end_of_day}
            })
            conversation_data.append(conv_count)
            
            resolved_count = mongo.db.conversations.count_documents({
                'resolved_at': {'$gte': start_of_day, '$lt': end_of_day}
            })
            resolved_data.append(resolved_count)
        
        # Reverse to show chronological order
        days.reverse()
        conversation_data.reverse()
        resolved_data.reverse()
        
        # Channel distribution
        channel_data = mongo.db.conversations.aggregate([
            {'$group': {
                '_id': '$channel',
                'count': {'$sum': 1}
            }}
        ])
        channel_data = [{item['_id'], item['count']} for item in channel_data]
        
        # Intent distribution
        intent_data = mongo.db.conversations.aggregate([
            {'$match': {
                'category': {'$exists': True, '$ne': None}
            }},
            {'$group': {
                '_id': '$category',
                'count': {'$sum': 1}
            }}
        ])
        intent_data = [{item['_id'], item['count']} for item in intent_data]
        
        return jsonify({
            'daily_conversations': {
                'labels': days,
                'datasets': [
                    {
                        'label': 'New Conversations',
                        'data': conversation_data,
                        'borderColor': 'rgb(75, 192, 192)',
                        'backgroundColor': 'rgba(75, 192, 192, 0.2)'
                    },
                    {
                        'label': 'Resolved Conversations',
                        'data': resolved_data,
                        'borderColor': 'rgb(54, 162, 235)',
                        'backgroundColor': 'rgba(54, 162, 235, 0.2)'
                    }
                ]
            },
            'channel_distribution': {
                'labels': [item[0] for item in channel_data],
                'datasets': [{
                    'data': [item[1] for item in channel_data],
                    'backgroundColor': [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 205, 86, 0.8)'
                    ]
                }]
            },
            'intent_distribution': {
                'labels': [item[0] for item in intent_data],
                'datasets': [{
                    'data': [item[1] for item in intent_data],
                    'backgroundColor': [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)'
                    ]
                }]
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
