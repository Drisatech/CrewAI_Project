# main.py
from crewai import Crew
from agents import create_agents
from tasks import create_tasks, create_dynamic_task
from voice_handler import VoiceHandler, VoiceWebInterface
from multilingual_handler import MultilingualHandler
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import threading
import re
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables
voice_handler = None
voice_web_interface = None
multilingual = None
agents = None
crew = None

def initialize_crew():
    """Initialize CrewAI components"""
    global agents, crew
    
    # Create agents
    agents = create_agents()
    
    # Create basic tasks
    tasks = create_tasks(agents)
    
    # Create crew
    crew = Crew(
        agents=list(agents.values()),
        tasks=list(tasks.values()),
        verbose=True,
        memory=True
    )
    
    print("CrewAI initialized successfully!")

def parse_voice_command(command_data: dict) -> dict:
    """Parse voice command data from multilingual handler"""
    if isinstance(command_data, str):
        # Fallback for simple string commands
        return {
            'intent': 'general',
            'query': command_data,
            'language': 'english',
            'confidence': 0.5
        }
    
    # Extract information from multilingual parsing
    original_text = command_data.get('original_text', '')
    detected_language = command_data.get('detected_language', 'english')
    translated_text = command_data.get('translated_text', original_text)
    intent_data = command_data.get('intent', {})
    
    return {
        'intent': intent_data.get('type', 'general'),
        'query': intent_data.get('query', translated_text),
        'product': intent_data.get('product', ''),
        'language': detected_language,
        'confidence': intent_data.get('confidence', 0.5),
        'original_text': original_text,
        'translated_text': translated_text
    }

def process_voice_command(command_data) -> str:
    """Process voice command using CrewAI agents with multilingual support"""
    global agents, crew, multilingual
    
    if not agents or not crew:
        return multilingual.get_response_text('error_occurred') if multilingual else "System not initialized. Please try again later."
    
    # Parse command data
    if isinstance(command_data, str):
        # Handle simple string input
        parsed = {'intent': 'general', 'query': command_data, 'language': 'english'}
    else:
        # Handle multilingual command data
        parsed = parse_voice_command(command_data)
    
    intent = parsed.get('intent')
    language = parsed.get('language', 'english')
    
    try:
        if intent == 'search':
            # Create dynamic search task
            query = parsed.get('query') or parsed.get('translated_text', '')
            task = create_dynamic_task('search', agents, query=query)
            result = crew.kickoff_for_each([{'voice_command': query}])
            
            # Format response in appropriate language
            if multilingual:
                response = multilingual.get_response_text('product_found', language, count=5)
                return f"{response}: {result}"
            else:
                return f"Here's what I found: {result}"
        
        elif intent == 'post':
            product = parsed.get('product', '')
            if multilingual:
                response = multilingual.get_response_text('posting_product', language)
                return f"{response}. {multilingual.get_response_text('description_question', language)}"
            else:
                return f"I can help you post your {product}. Please provide more details like price, location, and description."
        
        elif intent == 'register':
            if multilingual:
                return multilingual.get_response_text('registration_success', language)
            else:
                return "I can help you create an account. Please provide your username, email, and password."
        
        elif intent == 'login':
            if multilingual:
                return multilingual.get_response_text('login_success', language)
            else:
                return "I can help you log in. Please provide your username and password."
        
        else:
            # General assistance
            original_text = parsed.get('original_text', parsed.get('query', ''))
            result = crew.kickoff({'voice_command': original_text})
            return str(result)
    
    except Exception as e:
        print(f"Error processing command: {e}")
        if multilingual:
            return multilingual.get_response_text('error_occurred', language)
        else:
            return "I'm sorry, I encountered an error processing your request. Please try again."

# Flask Routes
@app.route('/')
def index():
    """Main page with voice interface"""
    return render_template('index.html')

@app.route('/api/voice/process', methods=['POST'])
def process_voice():
    """Process voice input from web interface with multilingual support"""
    try:
        if 'audio' in request.files:
            # Handle audio file upload
            audio_file = request.files['audio']
            temp_path = f"temp_audio_{int(time.time())}.wav"
            audio_file.save(temp_path)
            
            # Process audio with multilingual analysis
            result = voice_web_interface.process_voice_input(temp_path)
            os.remove(temp_path)
            
            if result['success']:
                command_data = result['parsed_command']
                response_text = process_voice_command(command_data)
                response_language = command_data.get('detected_language', 'english')
                
                # Generate voice response in detected language
                voice_file = voice_web_interface.generate_voice_response(response_text, response_language)
                
                return jsonify({
                    'success': True,
                    'command': result['text'],
                    'parsed_command': command_data,
                    'response': response_text,
                    'language': response_language,
                    'voice_file': voice_file
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result['error']
                })
        
        elif 'text' in request.json:
            # Handle text input with language detection
            command_text = request.json['text']
            user_language = request.json.get('language', 'auto')
            
            # Parse multilingual command
            if multilingual:
                command_data = multilingual.parse_multilingual_command(command_text)
            else:
                command_data = command_text
            
            response_text = process_voice_command(command_data)
            
            # Determine response language
            if isinstance(command_data, dict):
                response_language = command_data.get('detected_language', 'english')
            else:
                response_language = user_language if user_language != 'auto' else 'english'
            
            # Generate voice response
            voice_file = voice_web_interface.generate_voice_response(response_text, response_language)
            
            return jsonify({
                'success': True,
                'command': command_text,
                'response': response_text,
                'language': response_language,
                'voice_file': voice_file
            })
        
        else:
            return jsonify({
                'success': False,
                'error': 'No audio file or text provided'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/voice/response/<filename>')
def get_voice_response(filename):
    """Serve generated voice response files"""
    try:
        return send_file(f"static/voice_responses/{filename}", as_attachment=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for product search"""
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Create and execute search task
        task = create_dynamic_task('search', agents, query=query)
        result = crew.kickoff_for_each([{'query': query}])
        
        return jsonify({
            'success': True,
            'query': query,
            'results': str(result)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/post', methods=['POST'])
def api_post_product():
    """API endpoint for posting products"""
    try:
        data = request.json
        required_fields = ['title', 'description', 'price', 'location']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create and execute post task
        task = create_dynamic_task('post_product', agents, **data)
        result = crew.kickoff_for_each([data])
        
        return jsonify({
            'success': True,
            'message': 'Product posted successfully',
            'result': str(result)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    """API endpoint for user registration"""
    try:
        data = request.json
        required_fields = ['username', 'email', 'password']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create and execute registration task
        task = create_dynamic_task('register', agents, **data)
        result = crew.kickoff_for_each([data])
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'result': str(result)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for user login"""
    try:
        data = request.json
        required_fields = ['username', 'password']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create and execute login task
        task = create_dynamic_task('login', agents, **data)
        result = crew.kickoff_for_each([data])
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'result': str(result)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get available languages"""
    if multilingual:
        return jsonify(multilingual.get_available_languages())
    else:
        return jsonify({
            'languages': [{'code': 'english', 'name': 'English', 'native_name': 'English'}],
            'current': 'english'
        })

@app.route('/api/language/set', methods=['POST'])
def set_language():
    """Set user's preferred language"""
    try:
        data = request.json
        language = data.get('language', 'english')
        
        if multilingual:
            multilingual.current_language = language
        
        return jsonify({
            'success': True,
            'language': language,
            'greeting': multilingual.get_greeting('hello', language) if multilingual else 'Hello!'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_continuous_voice_listening():
    """Start continuous voice listening in a separate thread with multilingual support"""
    global voice_handler
    
    if voice_handler:
        def voice_callback(command_data):
            return process_voice_command(command_data)
        
        # Multilingual wake words
        wake_words = {
            'english': "hey farmdepot",
            'hausa': "kai farmdepot",
            'igbo': "ndewo farmdepot",
            'yoruba': "eku farmdepot"
        }
        
        voice_thread = threading.Thread(
            target=voice_handler.continuous_listening,
            args=(voice_callback, wake_words),
            daemon=True
        )
        voice_thread.start()
        print("Multilingual continuous voice listening started!")

if __name__ == '__main__':
    print("Initializing FarmDepot.ng Multilingual Voice Assistant...")
    
    # Initialize voice components
    try:
        voice_handler = VoiceHandler()
        voice_web_interface = VoiceWebInterface(voice_handler)
        multilingual = voice_handler.multilingual
        print("Voice components with multilingual support initialized!")
    except Exception as e:
        print(f"Warning: Voice components failed to initialize: {e}")
        print("Voice features will be limited.")
    
    # Initialize CrewAI
    initialize_crew()
    
    # Start continuous voice listening (optional)
    if voice_handler and os.getenv('ENABLE_CONTINUOUS_LISTENING', 'false').lower() == 'true':
        start_continuous_voice_listening()
    
    # Start Flask app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"Starting multilingual server on port {port}...")
    print("Supported languages: English, Hausa, Igbo, Yoruba")
    app.run(host='0.0.0.0', port=port, debug=debug)