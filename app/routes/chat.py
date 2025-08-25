"""
Chat routes for web interface
"""

from flask import Blueprint, render_template, request, session
import uuid

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
def index():
    """Main chat interface"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    return render_template('chat.html', session_id=session['session_id'])

@chat_bp.route('/chat')
def chat_page():
    """Chat page route"""
    return render_template('chat.html')
