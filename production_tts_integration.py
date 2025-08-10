# production_tts_integration.py
# Integration file to replace the basic TTS in your existing system

import os
import asyncio
from typing import Optional
from advanced_tts_handler import AdvancedTTSHandler
from multilingual_handler import MultilingualHandler

class ProductionVoiceHandler:
    """Production-ready voice handler with advanced TTS"""
    
    def __init__(self):
        # Initialize existing components
        import speech_recognition as sr
        import whisper
        import pygame
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.whisper_model = whisper.load_model("base")
        self.multilingual = MultilingualHandler()
        
        # Initialize advanced TTS
        self.advanced_tts = AdvancedTTSHandler()
        self.tts_cache = TTSCache()
        
        pygame.mixer.init()
        
        # Calibrate microphone
        with self.microphone as source:
            print("Calibrating microphone...")
            self.recognizer.adjust_for_ambient_noise(source)
            print("Microphone calibrated!")
    
    def text_to_speech_production(self, text: str, language: str = None) -> bool:
        """Production TTS with caching and fallbacks"""
        if language is None:
            language = self.multilingual.current_language
        
        try:
            # Check cache first
            cached_audio = self.tts_cache.get_cached_audio(text, language)
            if cached_audio:
                print(f"Using cached audio for: {text[:50]}...")
                return self.play_cached_audio(cached_audio)
            
            # Adapt text for Nigerian context
            adapted_text = self.adapt_text_for_nigerian_context(text, language)
            
            # Generate speech with advanced TTS
            audio_file = self.advanced_tts.synthesize_speech(adapted_text, language, 'friendly')
            
            if audio_file:
                # Cache the generated audio
                self.tts_cache.cache_audio(text, language, audio_file)
                
                # Play audio
                return self.advanced_tts.play_audio(audio_file)
            else:
                # Fallback to basic TTS
                print(f"Advanced TTS failed, falling back to basic TTS for language: {language}")
                return self.basic_text_to_speech(text, language)
                
        except Exception as e:
            print(f"Production TTS error: {e}")
            # Final fallback
            return self.basic_text_to_speech(text, language)
    
    def adapt_text_for_nigerian_context(self, text: str, language: str) -> str:
        """Adapt text for Nigerian context and culture"""
        import re
        
        adapted_text = text
        
        # Currency formatting
        adapted_text = re.sub(r'\$(\d+)', r'₦\1', adapted_text)
        adapted_text = re.sub(r'(\d+)\s*dollars?', r'₦\1', adapted_text, flags=re.IGNORECASE)
        
        # Nigerian English adaptations
        if language == 'english':
            adaptations = {
                'gasoline': 'petrol',
                'elevator': 'lift',
                'apartment': 'flat',
                'truck': 'lorry',
                'corn': 'maize'
            }
            for american, nigerian in adaptations.items():
                adapted_text = re.sub(rf'\b{american}\b', nigerian, adapted_text, flags=re.IGNORECASE)
        
        # Add appropriate greetings based on time of day
        import datetime
        current_hour = datetime.datetime.now().hour
        
        if adapted_text.lower().startswith('welcome'):
            greetings = {
                'english': 'Welcome' if 6 <= current_hour < 18 else 'Good evening, welcome',
                'hausa': 'Sannu da zuwa' if 6 <= current_hour < 18 else 'Barka da yamma, sannu da zuwa',
                'igbo': 'Ndewo' if 6 <= current_hour < 18 else 'Mgbede ọma, ndewo',
                'yoruba': 'Eku abo' if 6 <= current_hour < 18 else 'Eku ale, eku abo'
            }
            
            if language in greetings:
                adapted_text = adapted_text.replace('Welcome', greetings[language], 1)
        
        # Apply pronunciation improvements
        adapted_text = self.apply_pronunciation_rules(adapted_text, language)
        
        return adapted_text
    
    def apply_pronunciation_rules(self, text: str, language: str) -> str:
        """Apply pronunciation rules for better TTS output"""
        
        # Nigerian place names pronunciation
        place_pronunciations = {
            'Lagos': 'LAY-gos',
            'Abuja': 'ah-BOO-jah',
            'Kano': 'KAH-no',
            'Ibadan': 'ee-bah-DAHN',
            'Kaduna': 'kah-DOO-nah'
        }
        
        for place, pronunciation in place_pronunciations.items():
            if place in text:
                # Use SSML phoneme for better pronunciation
                text = text.replace(place, f'<phoneme alphabet="ipa" ph="{pronunciation}">{place}</phoneme>')
        
        # Nigerian currency pronunciation
        text = re.sub(r'₦(\d+)', r'<say-as interpret-as="currency" language="en-NG">NGN \1</say-as>', text)
        
        # Agricultural terms with better pronunciation
        agricultural_terms = {
            'cassava': 'kah-SAH-vah',
            'plantain': 'PLAN-tin',
            'yam': 'YAHM'
        }
        
        for term, pronunciation in agricultural_terms.items():
            if term in text.lower():
                pattern = re.compile(rf'\b{term}\b', re.IGNORECASE)
                text = pattern.sub(f'<phoneme alphabet="ipa" ph="{pronunciation}">{term}</phoneme>', text)
        
        return text
    
    def basic_text_to_speech(self, text: str, language: str) -> bool:
        """Fallback to basic TTS (your original implementation)"""
        try:
            from gtts import gTTS
            import tempfile
            import pygame
            import time
            
            # Use appropriate language code
            lang_codes = {
                'english': 'en',
                'hausa': 'en',     # Fallback to English
                'igbo': 'en',      # Fallback to English
                'yoruba': 'en',    # Fallback to English
            }
            
            lang_code = lang_codes.get(language, 'en')
            tts = gTTS(text=text, lang=lang_code, slow=False)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tts.save(tmp_file.name)
                
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                os.unlink(tmp_file.name)
                return True
                
        except Exception as e:
            print(f"Basic TTS error: {e}")
            return False
    
    def play_cached_audio(self, audio_file: str) -> bool:
        """Play cached audio file"""
        if os.path.exists(audio_file):
            return self.advanced_tts.play_audio(audio_file)
        return False
    
    # Keep all your existing methods for speech recognition
    def listen_for_wake_word(self, wake_word: str = "hey farmdepot") -> bool:
        """Your existing implementation"""
        try:
            with self.microphone as source:
                print(f"Listening for wake word: '{wake_word}'...")
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                
            text = self.recognize_speech(audio)
            if text and wake_word.lower() in text.lower():
                print(f"Wake word detected: {text}")
                return True
            return False
        except Exception as e:
            print(f"Error listening for wake word: {e}")
            return False
    
    def recognize_speech(self, audio) -> Optional[str]:
        """Your existing speech recognition implementation"""
        try:
            # Try Google Speech Recognition first
            try:
                text = self.recognizer.recognize_google(audio)
                return text
            except:
                pass
            
            # Fallback to Whisper
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio.get_wav_data())
                tmp_file.flush()
                
                result = self.whisper_model.transcribe(tmp_file.name)
                os.unlink(tmp_file.name)
                
                return result["text"].strip() if result["text"].strip() else None
                
        except Exception as e:
            print(f"Speech recognition error: {e}")
            return None


class TTSCache:
    """Redis-based caching for TTS audio files"""
    
    def __init__(self):
        try:
            import redis
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 2)),
                decode_responses=False
            )
            self.ttl = int(os.getenv('TTS_CACHE_TTL', 3600))  # 1 hour default
            self.cache_enabled = os.getenv('TTS_CACHE_ENABLED', 'true').lower() == 'true'
        except ImportError:
            print("Redis not available, disabling TTS cache")
            self.redis_client = None
            self.cache_enabled = False
    
    def get_cached_audio(self, text: str, language: str) -> Optional[str]:
        """Get cached audio file path"""
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            import hashlib
            cache_key = f"tts:{hashlib.md5(f'{text}:{language}'.encode()).hexdigest()}"
            cached_path = self.redis_client.get(cache_key)
            
            if cached_path:
                cached_path = cached_path.decode()
                if os.path.exists(cached_path):
                    return cached_path
                else:
                    # Remove stale cache entry
                    self.redis_client.delete(cache_key)
            
            return None
        except Exception as e:
            print(f"Cache retrieval error: {e}")
            return None
    
    def cache_audio(self, text: str, language: str, audio_path: str):
        """Cache audio file path"""
        if not self.cache_enabled or not self.redis_client:
            return
        
        try:
            import hashlib
            cache_key = f"tts:{hashlib.md5(f'{text}:{language}'.encode()).hexdigest()}"
            
            # Create permanent cache directory
            cache_dir = os.path.join('static', 'tts_cache')
            os.makedirs(cache_dir, exist_ok=True)
            
            # Copy file to cache directory
            import shutil
            cached_file = os.path.join(cache_dir, f"{cache_key.split(':')[1]}.mp3")
            shutil.copy2(audio_path, cached_file)
            
            # Store in Redis
            self.redis_client.setex(cache_key, self.ttl, cached_file)
            
        except Exception as e:
            print(f"Cache storage error: {e}")


class AsyncTTSHandler:
    """Asynchronous TTS for better performance"""
    
    def __init__(self, voice_handler: ProductionVoiceHandler):
        self.voice_handler = voice_handler
        self.executor = None
    
    async def synthesize_async(self, text: str, language: str) -> bool:
        """Asynchronous TTS synthesis"""
        if self.executor is None:
            from concurrent.futures import ThreadPoolExecutor
            self.executor = ThreadPoolExecutor(max_workers=2)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.voice_handler.text_to_speech_production,
            text,
            language
        )
    
    async def preload_common_phrases(self):
        """Preload common phrases for faster response"""
        common_phrases = {
            'english': [
                "Welcome to FarmDepot.ng",
                "I found several products matching your search",
                "Please provide more details about your product",
                "Thank you for using our service"
            ],
            'hausa': [
                "Maraba da zuwa FarmDepot.ng",
                "Na sami kayayyaki da yawa da suka dace da binciken ku",
                "Da fatan za ku ba da ƙarin bayani game da kayan ku",
                "Na gode da amfani da sabis ɗin mu"
            ],
            'igbo': [
                "Ndewo na FarmDepot.ng",
                "Achọtara m ọtụtụ ngwaahịa dabara na nchọgharị gị",
                "Biko nye nkọwa ndị ọzọ gbasara ngwaahịa gị",
                "Daalụ maka iji ọrụ anyị"
            ],
            'yoruba': [
                "Eku abo si FarmDepot.ng",
                "Mo ri ọpọlọpọ oja ti o baamu pelu wiwa yin",
                "Jọwọ pese alaye diẹ sii nipa oja yin",
                "E se fun lilo iṣẹ wa"
            ]
        }
        
        tasks = []
        for language, phrases in common_phrases.items():
            for phrase in phrases:
                task = self.synthesize_async(phrase, language)
                tasks.append(task)
        
        # Execute all preload tasks
        await asyncio.gather(*tasks, return_exceptions=True)
        print("Common phrases preloaded successfully!")


# Usage in your main application
def upgrade_to_production_tts():
    """Upgrade your existing system to use production TTS"""
    
    # Replace your existing VoiceHandler initialization
    global voice_handler, voice_web_interface
    
    try:
        print("Upgrading to production TTS system...")
        
        # Initialize production voice handler
        voice_handler = ProductionVoiceHandler()
        
        # Initialize async TTS for better performance
        async_tts = AsyncTTSHandler(voice_handler)
        
        # Preload common phrases
        asyncio.run(async_tts.preload_common_phrases())
        
        print("Production TTS system initialized successfully!")
        print("Available engines:", list(voice_handler.advanced_tts.engines.keys()))
        
        # Test with a sample
        test_result = voice_handler.text_to_speech_production(
            "Production TTS system is now active", 
            "english"
        )
        
        if test_result:
            print("✅ Production TTS test successful!")
        else:
            print("⚠️  Production TTS test failed, but fallbacks are available")
            
    except Exception as e:
        print(f"Production TTS initialization error: {e}")
        print("Falling back to basic TTS system")