"""
Voice IVR routes using Twilio
"""

from flask import Blueprint, request, Response
from twilio.twiml.voice_response import VoiceResponse
from app import mongo
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.ai_service import HotelAIService
import uuid

voice_bp = Blueprint('voice', __name__)
ai_service = HotelAIService()

@voice_bp.route('/webhook', methods=['POST'])
def voice_webhook():
    """Handle incoming voice calls from Twilio"""
    response = VoiceResponse()
    
    # Get caller information
    caller_number = request.form.get('From')
    call_sid = request.form.get('CallSid')
    
    # Welcome message
    response.say(
        "Welcome to Grand Hotel customer service. I'm your AI assistant. "
        "Please speak your request after the tone.",
        voice='alice'
    )
    
    # Record the caller's message
    response.record(
        action='/voice/process',
        method='POST',
        max_length=30,
        finish_on_key='#'
    )
    
    return str(response)

@voice_bp.route('/process', methods=['POST'])
def process_voice():
    """Process recorded voice message"""
    response = VoiceResponse()
    
    try:
        # Get recording URL and transcription
        recording_url = request.form.get('RecordingUrl')
        caller_number = request.form.get('From')
        call_sid = request.form.get('CallSid')
        
        # For demo purposes, we'll use a placeholder transcription
        # In production, you'd use speech-to-text service
        transcription = "I need help with my room reservation"
        
        # Create or get user
        user_data = mongo.db.users.find_one({'phone': caller_number})
        if not user_data:
            user_id = str(uuid.uuid4())
            user_data = {
                '_id': user_id,
                'session_id': call_sid,
                'phone': caller_number,
                'guest_type': 'caller'
            }
            mongo.db.users.insert_one(user_data)
        else:
            user_id = user_data['_id']
        
        # Create conversation
        conversation_id = str(uuid.uuid4())
        conversation_data = {
            '_id': conversation_id,
            'user_id': user_id,
            'channel': 'voice',
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        mongo.db.conversations.insert_one(conversation_data)
        
        # Save user message
        user_message_data = {
            '_id': str(uuid.uuid4()),
            'conversation_id': conversation_id,
            'user_id': user_id,
            'sender_type': 'user',
            'message_text': transcription,
            'message_type': 'audio',
            'created_at': datetime.utcnow(),
            'metadata': {'recording_url': recording_url}
        }
        mongo.db.messages.insert_one(user_message_data)
        
        # Generate AI response
        ai_response = ai_service.generate_response(
            transcription,
            conversation_id,
            {'phone': caller_number}
        )
        
        # Save AI response
        ai_message_data = {
            '_id': str(uuid.uuid4()),
            'conversation_id': conversation_id,
            'sender_type': 'ai',
            'message_text': ai_response['response'],
            'created_at': datetime.utcnow(),
            'intent': ai_response.get('intent'),
            'confidence': ai_response.get('confidence')
        }
        mongo.db.messages.insert_one(ai_message_data)
        
        # Speak the response
        response.say(ai_response['response'], voice='alice')
        
        # Check if escalation is needed
        if ai_response.get('escalate'):
            response.say(
                "I'm transferring you to a human agent who can better assist you. "
                "Please hold while I connect you.",
                voice='alice'
            )
            # In production, you'd dial the hotel's customer service number
            response.dial('+1234567890')  # Hotel's customer service number
        else:
            # Ask if they need more help
            response.say(
                "Is there anything else I can help you with? "
                "Press 1 for yes, or hang up if you're satisfied.",
                voice='alice'
            )
            
            gather = response.gather(
                action='/voice/continue',
                method='POST',
                num_digits=1,
                timeout=10
            )
            
            response.say("Thank you for calling Grand Hotel. Have a great day!", voice='alice')
        
    except Exception as e:
        response.say(
            "I apologize, but I'm experiencing technical difficulties. "
            "Please call our front desk directly for immediate assistance.",
            voice='alice'
        )
    
    return str(response)

@voice_bp.route('/continue', methods=['POST'])
def continue_conversation():
    """Continue voice conversation"""
    response = VoiceResponse()
    
    digit_pressed = request.form.get('Digits')
    
    if digit_pressed == '1':
        response.say(
            "Please speak your next question after the tone.",
            voice='alice'
        )
        response.record(
            action='/voice/process',
            method='POST',
            max_length=30,
            finish_on_key='#'
        )
    else:
        response.say(
            "Thank you for calling Grand Hotel. Have a great day!",
            voice='alice'
        )
    
    return str(response)
