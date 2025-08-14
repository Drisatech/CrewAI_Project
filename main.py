# main.py - with OpenrouterAI
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import os
import requests
import traceback
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_openrouter_api(message, language='en', model="openai/gpt-4o-mini"):
    """Call OpenRouter API directly"""
    
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY not found in environment variables")
        return None
    
    # Language-specific system prompts
    system_prompts = {
        'en': """You are an expert Nigerian agricultural specialist. Provide practical, actionable farming advice specific to Nigerian conditions. Keep responses concise (2-3 paragraphs) and include specific varieties, timing, and techniques relevant to Nigeria's climate and soil conditions.""",
        
        'ha': """Ka zama gwani masanin aikin gona na Najeriya. Ka ba da shawarwarin aikin gona da suka dace da yanayin Najeriya. Ka yi amfani da Hausa mai saukin fahimta kuma ka ba da shawarwari masu amfani.""",
        
        'ig': """Ị bụ ọkachamara n'ihe gbasara ọrụ ugbo na Naịjirịa. Nye ndụmọdụ ọrụ ugbo bara uru nke kwesịrị ọnọdụ Naịjirịa. Jiri Igbo dị mfe nghọta ma nye ndụmọdụ bara uru.""",
        
        'yo': """O jẹ amoye ninu ise agbe ti Naijiria. Fun ni imọran ise agbe ti o wulo ti o baamu pẹlu ipo Naijiria. Lo Yoruba ti o rọrun lati ni oye ati fun imọran ti o wulo."""
    }
    
    system_prompt = system_prompts.get(language, system_prompts['en'])
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://farmdepot.ng",  # Your site URL
            "X-Title": "FarmDepot Voice Assistant",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": f"Question: {message}"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
        
        response = requests.post(
            OPENROUTER_BASE_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            else:
                logger.error(f"Unexpected OpenRouter response format: {data}")
                return None
        else:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"OpenRouter API call failed: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def process_farming_query(message, language='en'):
    """Process farming query using OpenRouter"""
    
    # Try OpenRouter API first
    response = call_openrouter_api(message, language)
    
    if response:
        return response
    else:
        # Fallback to keyword-based responses
        logger.warning("OpenRouter failed, using fallback responses")
        return generate_fallback_response(message, language)

def generate_fallback_response(message, language='en'):
    """Generate fallback response when OpenRouter is not available"""
    
    message_lower = message.lower()
    
    responses = {
        'en': {
            'maize': """For maize cultivation in Nigeria:
            
🌱 **Planting**: Plant during rainy season (May-July) using improved varieties like SAMMAZ-15, SAMMAZ-16, or local varieties like Oba Super 2.

📏 **Spacing**: 75cm between rows, 25cm between plants (about 53,000 plants per hectare).

🌿 **Fertilization**: Apply NPK 20:10:10 at planting (2 bags/hectare), then top-dress with Urea after 4-6 weeks (1 bag/hectare).

🌧️ **Water**: Needs 500-800mm of rainfall during growing season. Supplement with irrigation if rainfall is insufficient.""",
            
            'rice': """Rice cultivation guide for Nigeria:
            
🏞️ **Land**: Choose lowland (fadama) areas or prepare upland fields with good drainage.

🌱 **Varieties**: Use FARO varieties (FARO-44, FARO-52) or local varieties like Ofada for better market value.

💧 **Water Management**: For lowland rice, maintain 2-5cm water depth. For upland, ensure consistent moisture without waterlogging.

🌾 **Harvesting**: Ready for harvest 90-120 days after planting when grains turn golden yellow.""",
            
            'cassava': """Cassava farming in Nigeria:
            
🌿 **Varieties**: Use improved varieties like TMS-30572, TME-419, or NR-8082 for better yields and disease resistance.

🌱 **Planting**: Use 20cm stem cuttings, plant at 45° angle, 1m x 1m spacing (10,000 stands per hectare).

🌧️ **Season**: Plant early in rainy season (April-May) for best establishment.

⏰ **Harvest**: Ready after 12-18 months. Can leave in ground longer if needed as natural storage.""",
            
            'tomato': """Tomato production tips:
            
🌱 **Nursery**: Start seeds in nursery beds, transplant after 4-6 weeks when plants are 10-15cm tall.

🏞️ **Land**: Choose well-drained soil, add compost or organic matter before planting.

🌿 **Support**: Stake plants or use trellises for better growth and fruit quality.

🐛 **Pest Control**: Watch for whiteflies, aphids, and blight. Use neem-based products or IPM practices.""",
            
            'default': f"""Thank you for your farming question about '{message}'. 

For specific advice on Nigerian agriculture, I can help with:
• Crop cultivation (maize, rice, cassava, yam, tomato, etc.)
• Soil management and fertilization
• Pest and disease control
• Seasonal farming calendar
• Market prices and varieties

Please ask about a specific crop or farming challenge for detailed guidance."""
        },
        
        'ha': {
            'default': f"""Na gode da tambayarku game da noma: '{message}'.

Zan iya taimaka muku da:
• Noman amfanin gona (masara, shinkafa, rogo, doya, tumatir)
• Kula da ƙasa da takin zamani
• Yaƙi da kwari da cututtuka
• Lokacin shuki da girbi
• Farashi da nau'ikan iri-iri

Don samun cikakkun bayanai, ku tambaya game da takamaiman amfanin gona ko matsalar noma."""
        },
        
        'ig': {
            'default': f"""Dalu maka ajụjụ gị banyere ọrụ ugbo: '{message}'.

Enwere m ike inyere gị aka na:
• Ịkọ ihe ọkụkụ (ọka, osikapa, akpụ, ji, tomato)
• Nlekọta ala na fatịlaịza
• Ịlụso ụmụ ahụhụ na ọrịa ọgụ
• Oge ịkụ na ịghọta ihe ọkụkụ
• Ọnụahịa na ụdị mkpụrụ dị iche iche

Maka nkọwa zuru ezu, jụọ banyere ihe ọkụkụ akọwapụtara ma ọ bụ nsogbu ọrụ ugbo."""
        },
        
        'yo': {
            'default': f"""E se fun ibeere rẹ nipa ise agbe: '{message}'.

Mo le ran ọ lọwọ pẹlu:
• Gbingbin irugbin (agbado, iresi, gbaguda, isu, tomati)
• Itọju ile ati ajile
• Koja kokoro ati arun
• Akoko gbingbin ati ikore
• Owo ati oriṣiriṣi irugbin

Fun alaye pipe, beere nipa irugbin kan pato tabi iṣoro ise agbe kan."""
        }
    }
    
    lang_responses = responses.get(language, responses['en'])
    
    # Check for keywords
    for keyword, response in lang_responses.items():
        if keyword != 'default' and keyword in message_lower:
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
        'openrouter_configured': OPENROUTER_API_KEY is not None,
        'service': 'FarmDepot Voice Assistant'
    })

@app.route('/models', methods=['GET'])
def available_models():
    """Get available OpenRouter models"""
    if not OPENROUTER_API_KEY:
        return jsonify({'error': 'OpenRouter API key not configured'}), 500
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'error': 'Failed to fetch models'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        # Extract language and model
        language = data.get('language', 'en')
        model = data.get('model', 'openai/gpt-4o-mini')  # Default model
        
        logger.info(f"Processing message: {message} (language: {language}, model: {model})")
        
        # Process the farming query
        response_text = process_farming_query(message, language)
        
        if response_text:
            return jsonify({
                'response': response_text,
                'language': language,
                'model_used': model,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            })
        else:
            return jsonify({
                'error': 'Failed to generate response',
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }), 500
        
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

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Check OpenRouter configuration
    if OPENROUTER_API_KEY:
        logger.info("✅ OpenRouter API key configured")
    else:
        logger.warning("⚠️ OPENROUTER_API_KEY not found - using fallback responses only")
    
    # Get port from environment (required for Render)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False  # Set to False for production
    )