"""
AI Service for handling customer queries using LangChain and Google Gemini API
"""

import os
import time
from typing import Dict, List, Optional, Tuple
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    # Fallback for missing langchain-google-genai
    ChatGoogleGenerativeAI = None
try:
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.chains import ConversationChain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    # Fallback when langchain is not available
    LANGCHAIN_AVAILABLE = False
    HumanMessage = SystemMessage = AIMessage = None
    ConversationBufferWindowMemory = ChatPromptTemplate = MessagesPlaceholder = ConversationChain = None
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False
from app.models.mongo_models import Message, Conversation, GuestRequest
from app.models.analytics import Analytics
from app.services.document_service import DocumentService

class HotelAIService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            print("Warning: GOOGLE_API_KEY not found, using fallback responses")
            self.api_key = "fallback_mode"
        
        # Configure Gemini API
        if self.api_key != "fallback_mode" and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
            except Exception:
                print("Warning: Gemini API configuration failed, using fallback mode")
                self.api_key = "fallback_mode"
        
        # Initialize LangChain with Gemini
        if ChatGoogleGenerativeAI and self.api_key != "fallback_mode" and LANGCHAIN_AVAILABLE:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-pro",
                    google_api_key=self.api_key,
                    temperature=0.7,
                    max_tokens=1000
                )
            except Exception:
                print("Warning: LangChain initialization failed, using fallback mode")
                self.llm = None
        else:
            self.llm = None
        
        # Initialize document service for PDF queries
        self.document_service = DocumentService()
        
        # Hotel-specific system prompt
        self.system_prompt = self._create_system_prompt()
        
        # Enhanced intent classification patterns
        self.intents = {
            'booking': ['book', 'reserve', 'reservation', 'availability', 'room'],
            'complaint': ['complain', 'problem', 'issue', 'wrong', 'bad', 'terrible'],
            'inquiry': ['information', 'help', 'question', 'what', 'how', 'when'],
            'service_request': ['service', 'housekeeping', 'maintenance', 'room service'],
            'checkout': ['checkout', 'check out', 'leaving', 'bill', 'payment'],
            'amenities': ['pool', 'gym', 'spa', 'restaurant', 'wifi', 'parking'],
            'emergency': ['emergency', 'urgent', 'help', 'fire', 'medical'],
            'policy_inquiry': ['policy', 'rule', 'regulation', 'allowed', 'permitted', 'procedure'],
            'concierge_request': ['recommend', 'suggest', 'where', 'restaurant', 'attraction', 'tour'],
            'guest_request': ['need', 'want', 'request', 'arrange', 'schedule', 'order']
        }
    
    def _create_system_prompt(self) -> str:
        hotel_info = {
            'name': os.getenv('HOTEL_NAME', 'Grand Hotel'),
            'phone': os.getenv('HOTEL_PHONE', '+1234567890'),
            'email': os.getenv('HOTEL_EMAIL', 'info@grandhotel.com'),
            'address': os.getenv('HOTEL_ADDRESS', '123 Main St, City, State 12345')
        }
        
        return f"""You are a knowledgeable hotel concierge AI assistant for {hotel_info['name']}. Your primary role is to provide helpful, direct answers to guest questions and assist with their needs.

HOTEL INFORMATION:
- Name: {hotel_info['name']}
- Phone: {hotel_info['phone']}
- Email: {hotel_info['email']}
- Address: {hotel_info['address']}

YOUR ROLE:
- Answer guest questions directly and comprehensively
- Provide detailed information about hotel amenities, policies, and services
- Offer local recommendations and travel advice
- Handle service requests and bookings
- Share knowledge about hotel facilities, dining, spa services, etc.
- Give helpful tips and suggestions to enhance the guest experience

RESPONSE STYLE:
1. Always provide direct, helpful answers first
2. Be informative and specific in your responses
3. Share relevant details about hotel services and amenities
4. Offer practical solutions and alternatives
5. Use a warm, professional, and welcoming tone
6. Provide complete information rather than redirecting to front desk
7. Only suggest contacting staff for tasks that require human intervention (like actual bookings, emergencies, or complex issues)

WHEN TO ESCALATE TO HUMAN STAFF:
- Actual room bookings or reservations
- Billing issues or payment problems
- Medical emergencies or safety concerns
- Maintenance issues requiring immediate attention
- Complaints requiring manager intervention
- Complex requests needing special arrangements

EXAMPLE RESPONSES:
- For "What time is breakfast?" → Provide specific breakfast hours, location, menu highlights
- For "Do you have a gym?" → Describe gym facilities, hours, equipment available
- For "What's nearby?" → Give detailed local recommendations with distances and descriptions
- For "Can I get extra towels?" → Explain housekeeping procedures and how to request them

Remember: Be the helpful, knowledgeable concierge who provides valuable information and assistance. Only redirect to human staff when absolutely necessary."""

    def classify_intent(self, message: str) -> Tuple[str, float]:
        """Classify the intent of a user message"""
        message_lower = message.lower()
        intent_scores = {}
        
        for intent, keywords in self.intents.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                intent_scores[intent] = score / len(keywords)
        
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
            return best_intent, confidence
        
        return 'inquiry', 0.5  # Default intent

    def analyze_sentiment(self, message: str) -> str:
        """Basic sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'perfect', 'love', 'happy']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'angry', 'frustrated', 'disappointed']
        
        message_lower = message.lower()
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if negative_count > positive_count:
            return 'negative'
        elif positive_count > negative_count:
            return 'positive'
        return 'neutral'

    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve recent conversation history"""
        messages = list(mongo.db.messages.find({'conversation_id': conversation_id}).sort('created_at', -1).limit(limit))
        
        history = []
        for msg in reversed(messages):
            role = "assistant" if msg['sender_type'] == "ai" else "user"
            history.append({"role": role, "content": msg['message_text']})
        
        return history

    def search_hotel_documents(self, query: str) -> str:
        """Search hotel documents for relevant information"""
        try:
            results = self.document_service.search_documents(query, limit=3)
            if results:
                context = "Based on hotel documents:\n\n"
                for result in results:
                    context += f"- {result['content'][:300]}...\n\n"
                return context
            return ""
        except Exception:
            return ""

    def record_guest_request(self, conversation_id: str, user_id: str, 
                           user_message: str, intent: str, user_context: Dict) -> Optional[str]:
        """Record guest requests automatically"""
        try:
            # Define request types that should be recorded
            recordable_intents = ['service_request', 'guest_request', 'concierge_request']
            
            if intent in recordable_intents:
                guest_request_data = {
                    '_id': str(uuid.uuid4()),
                    'conversation_id': conversation_id,
                    'user_id': user_id,
                    'message': user_message,
                    'intent': intent,
                    'status': 'pending',
                    'priority': 'medium',
                    'created_at': datetime.utcnow(),
                    'user_context': user_context
                }
                mongo.db.guest_requests.insert_one(guest_request_data)
                return guest_request_data['_id']
                    

                return "Guest request recorded successfully."
            return None
        except Exception as e:
            print(f"Error recording guest request: {e}")
            return None




    def generate_response(self, user_message: str, conversation_id: str, 
                         user_context: Optional[Dict] = None) -> Dict:
        """Generate AI response using LangChain and Gemini"""
        start_time = time.time()
        
        try:
            # Classify intent and sentiment
            intent, confidence = self.classify_intent(user_message)
            sentiment = self.analyze_sentiment(user_message)
            
            # Get conversation history
            history = self.get_conversation_history(conversation_id)
            
            # Search hotel documents for relevant information
            document_context = self.search_hotel_documents(user_message)
            
            # Record guest request if applicable
            self.record_guest_request(
                conversation_id,
                user_id,
                user_message,
                intent,
                user_context
            )
            
            # Build context for the AI
            context_info = ""
            if user_context:
                if user_context.get('name'):
                    context_info += f"Guest Name: {user_context['name']}\n"
                if user_context.get('room_number'):
                    context_info += f"Room Number: {user_context['room_number']}\n"
                if user_context.get('guest_type'):
                    context_info += f"Guest Type: {user_context['guest_type']}\n"
            
            if document_context:
                context_info += f"\nRelevant Hotel Information:\n{document_context}"
            
            # Load conversation history and create memory if LangChain is available
            if LANGCHAIN_AVAILABLE:
                messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
                
                # Create memory with conversation history
                memory = ConversationBufferWindowMemory(
                    k=10,  # Keep last 10 exchanges
                    return_messages=True
                )
                
                # Add previous messages to memory
                for msg in messages[-20:]:  # Last 20 messages
                    if msg.sender == 'user':
                        memory.chat_memory.add_user_message(msg.content)
                    else:
                        memory.chat_memory.add_ai_message(msg.content)
                
                # Create prompt template
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self.system_prompt + f"\n\nCURRENT CONTEXT:\n{context_info}"),
                    MessagesPlaceholder(variable_name="history"),
                    ("human", "{input}")
                ])
            else:
                memory = None
                prompt = None
            
            # Generate response
            if self.llm and LANGCHAIN_AVAILABLE:
                # Create conversation chain
                conversation = ConversationChain(
                    llm=self.llm,
                    memory=memory,
                    prompt=prompt,
                    verbose=False
                )
                response = conversation.predict(input=user_message)
            else:
                # Fallback response when LangChain is not available
                response = self._generate_fallback_response(user_message, intent)
                
                # Add document context to fallback response if available
                if document_context:
                    response += f"\n\n{document_context}"
                
                # Add request confirmation if applicable
                if request_confirmation:
                    response += f"\n\n{request_confirmation}"
            
            processing_time = time.time() - start_time
            
            # Record analytics
            Analytics.record_metric('response_time', processing_time, metadata={
                'intent': intent,
                'confidence': confidence,
                'sentiment': sentiment
            })
            
            return {
                'response': response,
                'intent': intent,
                'confidence': confidence,
                'sentiment': sentiment,
                'processing_time': processing_time,
                'escalate': self._should_escalate(user_message, intent, sentiment)
            }
            
        except Exception as e:
            # Fallback response
            return {
                'response': "I apologize, but I'm experiencing technical difficulties. Please contact our front desk for immediate assistance.",
                'intent': 'error',
                'confidence': 0.0,
                'sentiment': 'neutral',
                'processing_time': time.time() - start_time,
                'escalate': True,
                'error': str(e)
            }

    def _should_escalate(self, message: str, intent: str, sentiment: str) -> bool:
        """Determine if conversation should be escalated to human agent"""
        escalation_triggers = [
            intent == 'emergency',
            sentiment == 'negative' and any(word in message.lower() 
                                          for word in ['manager', 'supervisor', 'complaint', 'refund']),
            'human' in message.lower() or 'agent' in message.lower(),
            'speak to someone' in message.lower()
        ]
        
        return any(escalation_triggers)

    def get_suggested_responses(self, intent: str) -> List[str]:
        """Get suggested quick responses based on intent"""
        suggestions = {
            'booking': [
                "I'd be happy to help you with your reservation. What dates are you looking for?",
                "Let me check our availability for you.",
                "Would you like to modify an existing reservation?"
            ],
            'complaint': [
                "I sincerely apologize for the inconvenience. Let me help resolve this immediately.",
                "I understand your concern. Can you provide more details so I can assist you better?",
                "I'd like to escalate this to our manager for immediate attention."
            ],
            'inquiry': [
                "I'm here to help! What would you like to know?",
                "I can provide information about our services and amenities.",
                "How can I assist you today?"
            ],
            'service_request': [
                "I'll arrange that service for you right away.",
                "Let me connect you with the appropriate department.",
                "What room number should I send the service to?"
            ]
        }
        
        return suggestions.get(intent, ["How can I help you today?"])
    
    def _generate_fallback_response(self, user_message: str, intent: str) -> str:
        """Generate a helpful fallback response when LangChain is not available"""
        message_lower = user_message.lower()
        
        # Hotel amenities and services information
        if any(word in message_lower for word in ['breakfast', 'dining', 'restaurant', 'food', 'dinner', 'lunch', 'eat']):
            if any(word in message_lower for word in ['want', 'need', 'order', 'get']):
                return "I'd be happy to help you with dining! Are you looking for room service or would you prefer to dine in our restaurant? For room service, I can help you place an order - what type of cuisine are you in the mood for? Also, could you please let me know your room number and any dietary preferences or allergies I should be aware of?"
            else:
                return "Our main restaurant serves breakfast from 6:30 AM to 10:30 AM, lunch from 12:00 PM to 3:00 PM, and dinner from 6:00 PM to 10:00 PM. We also have 24-hour room service available. Our breakfast buffet features fresh pastries, eggs made to order, and local specialties."
        
        elif any(word in message_lower for word in ['gym', 'fitness', 'workout', 'exercise']):
            return "Our fitness center is open 24/7 and features modern cardio equipment, free weights, and strength training machines. We also have yoga mats and towels available. The gym is located on the 2nd floor."
        
        elif any(word in message_lower for word in ['pool', 'swimming', 'swim']):
            return "Our outdoor pool is open from 6:00 AM to 10:00 PM daily. We have poolside service available and comfortable lounge chairs. The pool area also includes a hot tub that's perfect for relaxation."
        
        elif any(word in message_lower for word in ['wifi', 'internet', 'connection']):
            return "Complimentary high-speed WiFi is available throughout the hotel. The network name is 'GrandHotel_Guest' and no password is required. If you experience any connectivity issues, please let me know."
        
        elif any(word in message_lower for word in ['parking', 'car', 'valet']):
            return "We offer both self-parking ($15/night) and valet parking ($25/night). Valet service is available from 6:00 AM to midnight. Our parking garage is secure and covered."
        
        elif any(word in message_lower for word in ['spa', 'massage', 'wellness']):
            return "Our spa offers a full range of services including massages, facials, and body treatments. We're open daily from 9:00 AM to 8:00 PM. I'd recommend booking in advance as we tend to fill up quickly."
        
        elif any(word in message_lower for word in ['checkout', 'check out', 'leaving']):
            return "Checkout time is 11:00 AM. You can check out using the TV in your room, at the front desk, or through our mobile app. Late checkout until 2:00 PM is available for $50, subject to availability."
        
        elif any(word in message_lower for word in ['towels', 'housekeeping', 'cleaning']):
            if any(word in message_lower for word in ['want', 'need', 'get', 'extra']):
                return "I'll be happy to arrange that for you! Could you please let me know your room number and how many extra towels you'd like? Also, would you prefer bath towels, hand towels, or both? I'll have housekeeping bring them to your room right away."
            else:
                return "Housekeeping services are available daily. For extra towels, linens, or amenities, you can call housekeeping directly or request them through the phone in your room. We're happy to accommodate any special requests."
        
        elif any(word in message_lower for word in ['nearby', 'attractions', 'things to do', 'recommendations']):
            return "There's plenty to explore nearby! The historic downtown area is just 10 minutes away with great shopping and dining. The art museum is 15 minutes by car, and we're only 5 minutes from the beautiful riverside park. I can provide more specific recommendations based on your interests."
        
        elif any(word in message_lower for word in ['room service', 'food delivery']):
            if any(word in message_lower for word in ['want', 'need', 'order', 'get']):
                return "I'd love to help you with room service! What would you like to order today? We have appetizers, main courses, desserts, and beverages available. Could you also please provide your room number and let me know if you have any dietary restrictions or allergies I should be aware of?"
            else:
                return "Room service is available 24/7. You can order using the phone in your room or through our mobile app. Delivery typically takes 30-45 minutes. We have a full menu including appetizers, entrees, desserts, and beverages."
        
        elif any(word in message_lower for word in ['concierge', 'tickets', 'reservations']):
            return "Our concierge team can help with restaurant reservations, show tickets, transportation arrangements, and local recommendations. We're here from 7:00 AM to 10:00 PM daily and would be happy to assist with any special requests."
        
        # Check for general service requests
        elif any(word in message_lower for word in ['want', 'need', 'get', 'order', 'request']):
            return f"I'd be delighted to help you with that! To make sure I assist you properly, could you please provide a few more details? What specifically would you like, and what's your room number? This will help me arrange everything perfectly for you."
        
        # Default helpful response
        return f"Hello! I'm here to assist you with anything you need during your stay. What can I help you with today? Whether it's information about our amenities, making a request, or getting recommendations, I'm happy to help!"
