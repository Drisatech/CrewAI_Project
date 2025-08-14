# main.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import os
import traceback
from datetime import datetime

# Import your CrewAI components (adjust imports based on your project structure)
try:
    from crewai import Agent, Task, Crew, Process
    from langchain_openai import ChatOpenAI
    CREWAI_AVAILABLE = True
except ImportError:
    print("CrewAI not available - using fallback responses")
    CREWAI_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for CrewAI components
farming_crew = None
farming_expert = None

def initialize_crew():
    """Initialize CrewAI agents and crew"""
    global farming_crew, farming_expert
    
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available - using fallback mode")
        return False
    
    try:
        # Initialize OpenAI LLM
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            return False
        
        llm = ChatOpenAI(
            model="gpt-4-turbo",
            temperature=0.7,
            api_key=openai_api_key
        )
        
        # Create farming expert agent
        farming_expert = Agent(
            role="Agricultural Specialist",
            goal="Provide expert farming advice tailored to Nigerian agriculture",
            backstory="""You are an experienced agricultural specialist with deep knowledge of 
            Nigerian farming practices, crops, weather patterns, and market conditions.
            You speak fluent English, Hausa, Igbo, and Yoruba and provide practical, 
            actionable advice to farmers.""",
            llm=llm,
            verbose=True,
            allow_delegation=False
        )
        
        # Create crew
        farming_crew = Crew(
            agents=[farming_expert],
            tasks=[],  # Tasks will be created dynamically
            process=Process.sequential,
            verbose=2
        )
        
        logger.info("CrewAI components initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize CrewAI: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def process_with_crewai(message, language='en'):
    """Process message using CrewAI"""
    global farming_crew, farming_expert
    
    if not CREWAI_AVAILABLE or not farming_expert:
        # Fallback response when CrewAI is not available
        return generate_fallback_response(message, language)
    
    try:
        # Create task for the specific query
        task = Task(
            description=f"""
            Answer this farming question in {language}: "{message}"
            
            Provide practical, actionable advice that is:
            1. Specific to Nigerian agricultural conditions
            2. Culturally appropriate
            3. Easy to understand and implement
            4. Based on best farming practices
            
            If the language is not English, provide the response in that language.
            Keep the response concise but informative (2-3 paragraphs maximum).
            """,
            agent=farming_expert,
            expected_output="Practical farming advice in the requested language"
        )
        
        # Update crew with new task
        farming_crew.tasks = [task]
        
        # Execute the crew
        result = farming_crew.kickoff()
        
        return str(result)
        
    except Exception as e:
        logger.error(f"CrewAI processing error: {str(e)}")
        logger.error(traceback.format_exc())
        return generate_fallback_response(message, language)

def generate_fallback_response(message, language='en'):
    """Generate fallback response when CrewAI is not available"""
    
    # Simple keyword-based responses
    message_lower = message.lower()
    
    responses = {
        'en': {
            'maize': "For maize cultivation in Nigeria, plant during the rainy season (May-July). Use improved varieties like SAMMAZ-15 or SAMMAZ-16. Ensure proper spacing of 75cm between rows and 25cm between plants. Apply NPK fertilizer at planting and top-dress with urea after 4-6 weeks.",
            'rice': "Rice grows well in Nigeria's wetland and upland areas. For wetland rice, maintain 2-5cm water depth. Use certified seeds like FARO varieties. Apply basal fertilizer before transplanting and top-dress with urea at tillering and booting stages.",
            'cassava': "Cassava is drought-tolerant and grows in various soil types. Plant during the rains using 20cm stem cuttings. Space plants 1m x 1m apart. Harvest after 12-18 months. Popular varieties include TMS-30572 and TME-419.",
            'tomato': "Tomatoes need well-drained soil and regular watering. Start with nursery seedlings, then transplant after 4-6 weeks. Stake plants for support and apply organic fertilizer regularly. Watch for pests like whiteflies and diseases like blight.",
            'default': f"Thank you for your farming question: '{message}'. For specific advice on crop cultivation, pest control, or farming techniques in Nigeria, please provide more details about your location, crop type, or specific challenge you're facing."
        },
        'ha': {  # Hausa
            'default': f"Na gode da tambayarku game da noma: '{message}'. Don samun shawarwari na musamman game da noman amfanin gona, yaƙi da kwari, ko dabarun noma a Najeriya, da fatan za ku ba da ƙarin bayani game da yankinku."
        },
        'ig': {  # Igbo
            'default': f"Dalu maka ajụjụ gị banyere ọrụ ugbo: '{message}'. Maka ndụmọdụ akọwapụtara banyere ịkọ ihe ọkụkụ, ịlụso ụmụ ahụhụ ọgụ, ma ọ bụ usoro ọrụ ugbo na Naịjirịa, biko nye nkọwa ndị ọzọ."
        },
        'yo': {  # Yoruba
            'default': f"E se fun ibeere rẹ nipa ise agbe: '{message}'. Fun imọran pato lori gbingbin eso, ijakadi kokoro, tabi awọn ilana ise agbe ni Nigeria, jọwọ fun alaye siwaju si nipa agbegbe rẹ."
        }
    }
    
    lang_responses = responses.get(language, responses['en'])
    
    # Check for keywords
    for keyword, response in lang_responses.items():
        if keyword in message_lower:
            return response
    
    return lang_responses['default']

# Routes
@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'crewai_available': CREWAI_AVAILABLE,
        'crew_initialized': farming_crew is not None
    })

@app.route('/', methods=['POST'])
@app.route('/chat', methods=['POST'])
@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint for WordPress plugin"""
    try:
        # Get JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data received'
            }), 400
        
        # Extract message
        message = data.get('message') or data.get('query') or data.get('text')
        if not message:
            return jsonify({
                'error': 'No message found in request'
            }), 400
        
        # Extract language
        language = data.get('language', 'en')
        
        logger.info(f"Processing message: {message} (language: {language})")
        
        # Process with CrewAI or fallback
        response = process_with_crewai(message, language)
        
        return jsonify({
            'response': response,
            'language': language,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'error': f'Server error: {str(e)}',
            'timestamp': datetime.now().isoformat(),
            'status': 'error'
        }), 500

@app.route('/voice', methods=['POST'])
def voice_chat():
    """Voice endpoint (currently same as text chat)"""
    return chat()

# Voice processing functions (fixed)
def process_voice_input(audio_data, language='en'):
    """Process voice input - placeholder function"""
    # This would contain your actual voice processing logic
    return "Voice processing not implemented yet"

# Initialize CrewAI on startup
@app.before_first_request
def initialize_app():
    """Initialize the application"""
    logger.info("Initializing FarmDepot Voice Assistant...")
    success = initialize_crew()
    if success:
        logger.info("✅ CrewAI initialized successfully")
    else:
        logger.warning("⚠️ CrewAI initialization failed - using fallback mode")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize CrewAI
    initialize_crew()
    
    # Get port from environment (required for Render)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False  # Set to False for production
    )