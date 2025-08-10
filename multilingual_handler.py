# multilingual_handler.py
import re
from typing import Dict, Tuple, Optional
from gtts import gTTS
import json
import os

class MultilingualHandler:
    """Handle multiple Nigerian languages for voice interactions"""
    
    def __init__(self):
        self.supported_languages = {
            'english': {'code': 'en', 'gtts_code': 'en'},
            'hausa': {'code': 'ha', 'gtts_code': 'en'},  # Use English TTS with Hausa text
            'igbo': {'code': 'ig', 'gtts_code': 'en'},   # Use English TTS with Igbo text
            'yoruba': {'code': 'yo', 'gtts_code': 'en'}  # Use English TTS with Yoruba text
        }
        
        self.current_language = 'english'
        self.translations = self.load_translations()
        self.agricultural_terms = self.load_agricultural_terms()
        
    def load_translations(self) -> Dict:
        """Load translation dictionaries for different languages"""
        return {
            'greetings': {
                'english': {
                    'welcome': "Welcome to FarmDepot.ng Voice Assistant",
                    'hello': "Hello! How can I help you today?",
                    'goodbye': "Thank you for using FarmDepot.ng. Goodbye!",
                    'help': "I can help you search for products, post items, register, or navigate the site."
                },
                'hausa': {
                    'welcome': "Maraba da zuwa FarmDepot.ng Voice Assistant",
                    'hello': "Sannu! Yaya zan iya taimaka muku yau?",
                    'goodbye': "Na gode da amfani da FarmDepot.ng. Sai anjima!",
                    'help': "Zan iya taimaka muku neman kayayyaki, saka abubuwa, rajista, ko kewaya shafin."
                },
                'igbo': {
                    'welcome': "Ndewo na FarmDepot.ng Voice Assistant",
                    'hello': "Ndewo! Kedu ka m ga-esi nyere gị aka taa?",
                    'goodbye': "Daalụ maka iji FarmDepot.ng. Ndewo!",
                    'help': "Enwere m ike inyere gị aka ịchọ ngwaahịa, itinye ihe, debanye aha, ma ọ bụ ịgagharị saịtị."
                },
                'yoruba': {
                    'welcome': "Eku abo si FarmDepot.ng Voice Assistant",
                    'hello': "Eku ojo! Bawo ni mo se le ran yin lowo loni?",
                    'goodbye': "E se fun lilo FarmDepot.ng. O dabo!",
                    'help': "Mo le ran yin lowo lati wa awon oja, gbe nkan soke, forukosile, tabi rin kiri oju iwe naa."
                }
            },
            'responses': {
                'english': {
                    'product_found': "I found {count} products matching your search",
                    'no_products': "No products found for your search",
                    'posting_product': "I'll help you post your product. Please provide the details",
                    'registration_success': "Registration successful! Welcome to FarmDepot.ng",
                    'login_success': "Login successful! Welcome back",
                    'error_occurred': "Sorry, an error occurred. Please try again",
                    'not_understood': "I didn't understand. Please try again",
                    'price_question': "What is the price of your product?",
                    'location_question': "What is your location?",
                    'description_question': "Please describe your product"
                },
                'hausa': {
                    'product_found': "Na sami kayayyaki {count} da suka dace da binciken ku",
                    'no_products': "Babu kayayyakin da aka samu don binciken ku",
                    'posting_product': "Zan taimaka muku saka kayan ku. Da fatan za ku bayar da cikakkun bayanai",
                    'registration_success': "Rajista ya yi nasara! Maraba da zuwa FarmDepot.ng",
                    'login_success': "Shiga ya yi nasara! Maraba da dawowa",
                    'error_occurred': "Yi hakuri, kuskure ya faru. Da fatan za ku sake gwadawa",
                    'not_understood': "Ban fahimce ba. Da fatan za ku sake gwadawa",
                    'price_question': "Menene farashin kayan ku?",
                    'location_question': "Ina wurin ku?",
                    'description_question': "Da fatan ku bayyana kayan ku"
                },
                'igbo': {
                    'product_found': "Achọtara m ngwaahịa {count} dabara na nchọgharị gị",
                    'no_products': "Achọtaghị ngwaahịa ọ bụla maka nchọgharị gị",
                    'posting_product': "Aga m enyere gị aka itinye ngwaahịa gị. Biko nye nkọwa",
                    'registration_success': "Ndebanye aha gara nke ọma! Nnọọ na FarmDepot.ng",
                    'login_success': "Nbanye gara nke ọma! Nnọọ ọzọ",
                    'error_occurred': "Ndo, njehie mere. Biko nwalee ọzọ",
                    'not_understood': "Aghọtaghị m. Biko nwalee ọzọ",
                    'price_question': "Gịnị bụ ọnụ ahịa ngwaahịa gị?",
                    'location_question': "Olee ebe ị nọ?",
                    'description_question': "Biko kọwaa ngwaahịa gị"
                },
                'yoruba': {
                    'product_found': "Mo ri awon oja {count} ti o baamu pelu wiwa yin",
                    'no_products': "Ko si oja ti a ri fun wiwa yin",
                    'posting_product': "Emi yoo ran yin lowo lati gbe oja yin soke. E je k'o pese awon alaye",
                    'registration_success': "Iforukosile ti dari! Eku abo si FarmDepot.ng",
                    'login_success': "Iwole ti dari! Eku abo pada",
                    'error_occurred': "Ma binu, aṣiṣe kan waye. E je k'o tun gbiyanju",
                    'not_understood': "Emi ko loye. E je k'o tun gbiyanju",
                    'price_question': "Kini owo oja yin?",
                    'location_question': "Nibo l'o wa?",
                    'description_question': "E je k'o salaye oja yin"
                }
            },
            'product_categories': {
                'english': {
                    'grains': 'Grains & Cereals',
                    'roots': 'Root Crops',
                    'vegetables': 'Vegetables',
                    'fruits': 'Fruits',
                    'livestock': 'Livestock',
                    'equipment': 'Farm Equipment'
                },
                'hausa': {
                    'grains': 'Hatsi da Cereals',
                    'roots': 'Amfanin gonaki na tushe',
                    'vegetables': 'Kayan lambu',
                    'fruits': 'Yayyafi',
                    'livestock': 'Dabbobi',
                    'equipment': 'Kayan aikin gona'
                },
                'igbo': {
                    'grains': 'Ọka na Cereals',
                    'roots': 'Mkpụrụ nduru',
                    'vegetables': 'Akwụkwọ nri',
                    'fruits': 'Mkpụrụ osisi',
                    'livestock': 'Anụ ụlọ',
                    'equipment': 'Ngwa ọrụ ugbo'
                },
                'yoruba': {
                    'grains': 'Irugbin ati Cereals',
                    'roots': 'Irugbin gbongbo',
                    'vegetables': 'Efo',
                    'fruits': 'Eso',
                    'livestock': 'Ẹranko ọsin',
                    'equipment': 'Ẹrọ ọna'
                }
            }
        }
    
    def load_agricultural_terms(self) -> Dict:
        """Load agricultural terms in different languages"""
        return {
            'crops': {
                'english': {
                    'maize': 'maize', 'corn': 'maize', 'rice': 'rice', 'cassava': 'cassava',
                    'yam': 'yam', 'cocoa': 'cocoa', 'groundnut': 'groundnut', 'beans': 'beans',
                    'millet': 'millet', 'sorghum': 'sorghum', 'plantain': 'plantain',
                    'banana': 'banana', 'tomato': 'tomato', 'pepper': 'pepper', 'onion': 'onion'
                },
                'hausa': {
                    'masara': 'maize', 'shinkafa': 'rice', 'rogo': 'cassava', 'doya': 'yam',
                    'koko': 'cocoa', 'gyada': 'groundnut', 'wake': 'beans', 'gero': 'millet',
                    'dawa': 'sorghum', 'ayaba': 'plantain', 'tumatir': 'tomato',
                    'barkono': 'pepper', 'albasa': 'onion', 'kuli': 'groundnut'
                },
                'igbo': {
                    'ọka': 'maize', 'osikapa': 'rice', 'akpu': 'cassava', 'ji': 'yam',
                    'koko': 'cocoa', 'ahụekere': 'groundnut', 'agwa': 'beans',
                    'acha': 'millet', 'ọkpọkọ': 'sorghum', 'unere': 'plantain',
                    'tomato': 'tomato', 'ose': 'pepper', 'yabasị': 'onion'
                },
                'yoruba': {
                    'agbado': 'maize', 'iresi': 'rice', 'gbaguda': 'cassava', 'isu': 'yam',
                    'koko': 'cocoa', 'epa': 'groundnut', 'ewa': 'beans',
                    'oka': 'millet', 'ọka-baba': 'sorghum', 'ọgẹdẹ': 'plantain',
                    'tomati': 'tomato', 'ata': 'pepper', 'alubosa': 'onion'
                }
            },
            'livestock': {
                'english': {
                    'cattle': 'cattle', 'cow': 'cattle', 'goat': 'goat', 'sheep': 'sheep',
                    'chicken': 'chicken', 'fowl': 'chicken', 'pig': 'pig', 'fish': 'fish'
                },
                'hausa': {
                    'shanu': 'cattle', 'saniya': 'cattle', 'akuya': 'goat', 'tunkiya': 'sheep',
                    'kaza': 'chicken', 'kajin': 'chicken', 'alade': 'pig', 'kifi': 'fish'
                },
                'igbo': {
                    'ehi': 'cattle', 'nne-ehi': 'cattle', 'ewu': 'goat', 'atụrụ': 'sheep',
                    'ọkụkọ': 'chicken', 'ezi': 'pig', 'azụ': 'fish'
                },
                'yoruba': {
                    'malu': 'cattle', 'abo-malu': 'cattle', 'ewure': 'goat', 'agutan': 'sheep',
                    'adiye': 'chicken', 'elede': 'pig', 'eja': 'fish'
                }
            }
        }
    
    def detect_language(self, text: str) -> str:
        """Detect the language of input text"""
        text = text.lower().strip()
        
        # Check for language indicators
        hausa_indicators = [
            'sannu', 'maraba', 'yaya', 'zan iya', 'na', 'da', 'kayan', 'shinkafa', 'masara',
            'neman', 'saka', 'gona', 'rajista', 'shiga', 'babu', 'akwai', 'menene', 'ina'
        ]
        
        igbo_indicators = [
            'ndewo', 'kedu', 'enwere', 'aga', 'm', 'nye', 'ngwaahịa', 'osikapa', 'ọka',
            'chọ', 'tinye', 'ugbo', 'debanye', 'banye', 'ọ bụla', 'gịnị', 'olee'
        ]
        
        yoruba_indicators = [
            'eku', 'bawo', 'mo le', 'ran', 'lowo', 'oja', 'iresi', 'agbado',
            'wa', 'gbe', 'ọna', 'forukosile', 'wole', 'ko si', 'kini', 'nibo'
        ]
        
        # Count matches for each language
        hausa_count = sum(1 for indicator in hausa_indicators if indicator in text)
        igbo_count = sum(1 for indicator in igbo_indicators if indicator in text)
        yoruba_count = sum(1 for indicator in yoruba_indicators if indicator in text)
        
        # Determine language based on highest count
        if hausa_count > 0 and hausa_count >= igbo_count and hausa_count >= yoruba_count:
            return 'hausa'
        elif igbo_count > 0 and igbo_count >= yoruba_count:
            return 'igbo'
        elif yoruba_count > 0:
            return 'yoruba'
        else:
            return 'english'
    
    def translate_agricultural_terms(self, text: str, from_lang: str) -> str:
        """Translate agricultural terms to English for processing"""
        if from_lang == 'english':
            return text
        
        text_lower = text.lower()
        translated_text = text_lower
        
        # Translate crops
        if from_lang in self.agricultural_terms['crops']:
            for local_term, english_term in self.agricultural_terms['crops'][from_lang].items():
                if local_term in text_lower:
                    translated_text = translated_text.replace(local_term, english_term)
        
        # Translate livestock
        if from_lang in self.agricultural_terms['livestock']:
            for local_term, english_term in self.agricultural_terms['livestock'][from_lang].items():
                if local_term in text_lower:
                    translated_text = translated_text.replace(local_term, english_term)
        
        return translated_text
    
    def get_response_text(self, key: str, language: str = None, **kwargs) -> str:
        """Get response text in specified language"""
        if language is None:
            language = self.current_language
            
        if language not in self.translations['responses']:
            language = 'english'
        
        try:
            response = self.translations['responses'][language][key]
            if kwargs:
                response = response.format(**kwargs)
            return response
        except KeyError:
            # Fallback to English if key not found
            try:
                response = self.translations['responses']['english'][key]
                if kwargs:
                    response = response.format(**kwargs)
                return response
            except KeyError:
                return "Sorry, I couldn't process that request."
    
    def get_greeting(self, greeting_type: str, language: str = None) -> str:
        """Get greeting text in specified language"""
        if language is None:
            language = self.current_language
            
        if language not in self.translations['greetings']:
            language = 'english'
        
        try:
            return self.translations['greetings'][language][greeting_type]
        except KeyError:
            return self.translations['greetings']['english'].get(greeting_type, "Hello!")
    
    def parse_multilingual_command(self, text: str) -> Dict:
        """Parse command in any supported language"""
        # Detect language
        detected_lang = self.detect_language(text)
        self.current_language = detected_lang
        
        # Translate agricultural terms to English for processing
        translated_text = self.translate_agricultural_terms(text, detected_lang)
        
        # Parse command patterns in different languages
        intent = self.extract_intent(text, detected_lang)
        
        return {
            'original_text': text,
            'detected_language': detected_lang,
            'translated_text': translated_text,
            'intent': intent,
            'confidence': 0.8 if detected_lang != 'english' else 0.9
        }
    
    def extract_intent(self, text: str, language: str) -> Dict:
        """Extract intent from text based on language"""
        text_lower = text.lower()
        
        # Search patterns for different languages
        search_patterns = {
            'english': [
                r'(?:find|search|look for|show me|need|want)\s+(.+)',
                r'(?:do you have|is there)\s+(.+)',
                r'(.+?)\s+(?:available|for sale)'
            ],
            'hausa': [
                r'(?:neman|bincike|nuna|ina bukata)\s+(.+)',
                r'(?:akwai|ana da)\s+(.+)',
                r'(.+?)\s+(?:akwai|ana sayarwa)'
            ],
            'igbo': [
                r'(?:chọ|chọgharị|gosi|achọrọ)\s+(.+)',
                r'(?:ọ nwere|enwere)\s+(.+)',
                r'(.+?)\s+(?:dị|maka ire)'
            ],
            'yoruba': [
                r'(?:wa|wiwa|fi han|mo fe)\s+(.+)',
                r'(?:ṣe o ni|ṣe e wa)\s+(.+)',
                r'(.+?)\s+(?:wa|fun tita)'
            ]
        }
        
        # Post patterns
        post_patterns = {
            'english': [r'(?:post|list|sell|add)\s+(.+)'],
            'hausa': [r'(?:saka|jera|sayar)\s+(.+)'],
            'igbo': [r'(?:tinye|debanye|ree)\s+(.+)'],
            'yoruba': [r'(?:gbe|fi soke|ta)\s+(.+)']
        }
        
        # Check for search intent
        if language in search_patterns:
            for pattern in search_patterns[language]:
                match = re.search(pattern, text_lower)
                if match:
                    return {
                        'type': 'search',
                        'query': match.group(1).strip(),
                        'confidence': 0.9
                    }
        
        # Check for post intent
        if language in post_patterns:
            for pattern in post_patterns[language]:
                match = re.search(pattern, text_lower)
                if match:
                    return {
                        'type': 'post',
                        'product': match.group(1).strip(),
                        'confidence': 0.8
                    }
        
        # Default intent
        return {
            'type': 'general',
            'query': text_lower,
            'confidence': 0.5
        }
    
    def generate_multilingual_tts(self, text: str, language: str = None) -> str:
        """Generate text-to-speech in appropriate language"""
        if language is None:
            language = self.current_language
        
        # Use appropriate TTS settings
        tts_lang = self.supported_languages.get(language, {}).get('gtts_code', 'en')
        
        try:
            # For now, use English TTS for all languages
            # In production, you might want to use specialized TTS engines
            tts = gTTS(text=text, lang='en', slow=False)
            return tts
        except Exception as e:
            print(f"TTS Error: {e}")
            # Fallback TTS
            tts = gTTS(text=text, lang='en', slow=False)
            return tts
    
    def get_language_preference_from_request(self, user_agent: str = "", accept_language: str = "") -> str:
        """Detect language preference from HTTP headers"""
        # Simple detection based on Accept-Language header
        if 'ha' in accept_language.lower():
            return 'hausa'
        elif 'ig' in accept_language.lower():
            return 'igbo'
        elif 'yo' in accept_language.lower():
            return 'yoruba'
        else:
            return 'english'
    
    def format_price_with_currency(self, price: str, language: str = None) -> str:
        """Format price with appropriate currency symbol"""
        if language is None:
            language = self.current_language
        
        try:
            # Remove any non-numeric characters except decimal point
            clean_price = re.sub(r'[^\d.]', '', str(price))
            if clean_price:
                price_float = float(clean_price)
                formatted_price = "{:,.0f}".format(price_float)
                
                if language == 'hausa':
                    return f"Naira {formatted_price}"
                elif language == 'igbo':
                    return f"Naịra {formatted_price}"
                elif language == 'yoruba':
                    return f"Naira {formatted_price}"
                else:
                    return f"₦{formatted_price}"
            else:
                return price
        except ValueError:
            return str(price)
    
    def get_available_languages(self) -> Dict:
        """Get list of available languages"""
        return {
            'languages': [
                {'code': 'english', 'name': 'English', 'native_name': 'English'},
                {'code': 'hausa', 'name': 'Hausa', 'native_name': 'Hausa'},
                {'code': 'igbo', 'name': 'Igbo', 'native_name': 'Igbo'},
                {'code': 'yoruba', 'name': 'Yoruba', 'native_name': 'Yorùbá'}
            ],
            'current': self.current_language
        }