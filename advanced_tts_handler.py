# advanced_tts_handler.py
import os
import tempfile
import requests
import json
from typing import Optional, Dict, Any
from gtts import gTTS
import azure.cognitiveservices.speech as speechsdk
from google.cloud import texttospeech
import boto3
from pydub import AudioSegment
import pygame
import time

class AdvancedTTSHandler:
    """Advanced TTS handler with specialized engines for Nigerian languages"""
    
    def __init__(self):
        self.engines = {
            'azure': AzureTTSEngine(),
            'google_cloud': GoogleCloudTTSEngine(),
            'aws_polly': AWSPollyEngine(),
            'elevenlabs': ElevenLabsEngine(),
            'native_speech': NativeSpeechEngine(),
            'gtts': GTTSEngine()  # Fallback
        }
        
        # Priority order for each language
        self.engine_priority = {
            'english': ['azure', 'google_cloud', 'aws_polly', 'elevenlabs', 'gtts'],
            'hausa': ['azure', 'native_speech', 'elevenlabs', 'google_cloud', 'gtts'],
            'igbo': ['azure', 'native_speech', 'elevenlabs', 'google_cloud', 'gtts'],
            'yoruba': ['azure', 'native_speech', 'elevenlabs', 'google_cloud', 'gtts']
        }
        
        pygame.mixer.init()
    
    def synthesize_speech(self, text: str, language: str = 'english', voice_style: str = 'neutral') -> Optional[str]:
        """Synthesize speech using the best available engine for the language"""
        
        if language not in self.engine_priority:
            language = 'english'
        
        # Try engines in priority order
        for engine_name in self.engine_priority[language]:
            engine = self.engines.get(engine_name)
            if engine and engine.is_available():
                try:
                    audio_file = engine.synthesize(text, language, voice_style)
                    if audio_file:
                        return audio_file
                except Exception as e:
                    print(f"TTS Engine {engine_name} failed: {e}")
                    continue
        
        # If all engines fail, return None
        print(f"All TTS engines failed for language: {language}")
        return None
    
    def play_audio(self, audio_file: str) -> bool:
        """Play audio file"""
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            return True
        except Exception as e:
            print(f"Audio playback error: {e}")
            return False


class AzureTTSEngine:
    """Azure Cognitive Services TTS - Best for Nigerian languages"""
    
    def __init__(self):
        self.api_key = os.getenv('AZURE_SPEECH_KEY')
        self.region = os.getenv('AZURE_SPEECH_REGION', 'westus2')
        
        # Azure voices for Nigerian languages (as of 2024)
        self.voice_mapping = {
            'english': {
                'female': 'en-NG-EzinneNeural',  # Nigerian English female
                'male': 'en-NG-AbeoNeural',       # Nigerian English male
            },
            'hausa': {
                'female': 'ha-NG-AishaNeural',   # Hausa female (if available)
                'male': 'ha-NG-IsaNeural',       # Hausa male (if available)
            },
            'igbo': {
                'female': 'ig-NG-ChinenyeNeural', # Igbo female (if available)
                'male': 'ig-NG-EmekaNeural',     # Igbo male (if available)
            },
            'yoruba': {
                'female': 'yo-NG-AdetunyiNeural', # Yoruba female (if available)
                'male': 'yo-NG-KunmiNeural',     # Yoruba male (if available)
            }
        }
    
    def is_available(self) -> bool:
        return bool(self.api_key and self.region)
    
    def synthesize(self, text: str, language: str, voice_style: str = 'neutral') -> Optional[str]:
        """Synthesize speech using Azure TTS"""
        if not self.is_available():
            return None
        
        try:
            # Configure speech service
            speech_config = speechsdk.SpeechConfig(subscription=self.api_key, region=self.region)
            
            # Select voice
            voice = self._get_voice(language, 'female')  # Default to female voice
            if not voice:
                # Fallback to English if language not supported
                voice = self.voice_mapping['english']['female']
            
            speech_config.speech_synthesis_voice_name = voice
            
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
            
            # Generate SSML for better control
            ssml = self._generate_ssml(text, voice, voice_style)
            
            # Synthesize
            result = synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Save audio to temp file
                output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                output_file.write(result.audio_data)
                output_file.close()
                return output_file.name
            else:
                print(f"Azure TTS error: {result.reason}")
                return None
                
        except Exception as e:
            print(f"Azure TTS synthesis error: {e}")
            return None
    
    def _get_voice(self, language: str, gender: str = 'female') -> Optional[str]:
        """Get appropriate voice for language and gender"""
        if language in self.voice_mapping:
            return self.voice_mapping[language].get(gender)
        return None
    
    def _generate_ssml(self, text: str, voice: str, style: str) -> str:
        """Generate SSML for enhanced speech control"""
        # Add Nigerian English or local language specific pronunciation rules
        prosody_rate = "medium"
        prosody_pitch = "medium"
        
        if style == 'friendly':
            prosody_rate = "medium"
            prosody_pitch = "+5%"
        elif style == 'professional':
            prosody_rate = "slow"
            prosody_pitch = "medium"
        
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice}">
                <prosody rate="{prosody_rate}" pitch="{prosody_pitch}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        return ssml.strip()


class GoogleCloudTTSEngine:
    """Google Cloud Text-to-Speech - Good multilingual support"""
    
    def __init__(self):
        self.credentials_path = os.getenv('GOOGLE_CLOUD_CREDENTIALS_PATH')
        if self.credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
    
    def is_available(self) -> bool:
        return bool(self.credentials_path and os.path.exists(self.credentials_path))
    
    def synthesize(self, text: str, language: str, voice_style: str = 'neutral') -> Optional[str]:
        """Synthesize speech using Google Cloud TTS"""
        if not self.is_available():
            return None
        
        try:
            client = texttospeech.TextToSpeechClient()
            
            # Configure input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Select voice and language
            voice_params = self._get_voice_params(language)
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_params['language_code'],
                name=voice_params['name'],
                ssml_gender=voice_params['gender']
            )
            
            # Configure audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0.0
            )
            
            # Perform synthesis
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Save audio
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            output_file.write(response.audio_content)
            output_file.close()
            
            return output_file.name
            
        except Exception as e:
            print(f"Google Cloud TTS error: {e}")
            return None
    
    def _get_voice_params(self, language: str) -> Dict[str, Any]:
        """Get voice parameters for language"""
        voice_mapping = {
            'english': {
                'language_code': 'en-NG',  # Nigerian English
                'name': 'en-NG-Standard-A',
                'gender': texttospeech.SsmlVoiceGender.FEMALE
            },
            'hausa': {
                'language_code': 'en-US',  # Fallback to US English
                'name': 'en-US-Neural2-F',
                'gender': texttospeech.SsmlVoiceGender.FEMALE
            },
            # Add more as Google adds support
        }
        
        return voice_mapping.get(language, voice_mapping['english'])


class ElevenLabsEngine:
    """ElevenLabs TTS - High quality with voice cloning capabilities"""
    
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Custom voice IDs (you can clone Nigerian voices)
        self.custom_voices = {
            'english_nigeria_female': os.getenv('ELEVENLABS_ENGLISH_NG_FEMALE_ID'),
            'hausa_female': os.getenv('ELEVENLABS_HAUSA_FEMALE_ID'),
            'igbo_female': os.getenv('ELEVENLABS_IGBO_FEMALE_ID'),
            'yoruba_female': os.getenv('ELEVENLABS_YORUBA_FEMALE_ID'),
        }
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def synthesize(self, text: str, language: str, voice_style: str = 'neutral') -> Optional[str]:
        """Synthesize speech using ElevenLabs"""
        if not self.is_available():
            return None
        
        try:
            # Select voice ID
            voice_id = self._get_voice_id(language)
            if not voice_id:
                return None
            
            # API endpoint
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            # Headers
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            # Payload
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",  # Best multilingual model
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.2,  # Adjust based on voice_style
                    "use_speaker_boost": True
                }
            }
            
            # Make request
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                # Save audio
                output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                output_file.write(response.content)
                output_file.close()
                return output_file.name
            else:
                print(f"ElevenLabs API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"ElevenLabs synthesis error: {e}")
            return None
    
    def _get_voice_id(self, language: str) -> Optional[str]:
        """Get voice ID for language"""
        voice_mapping = {
            'english': self.custom_voices.get('english_nigeria_female'),
            'hausa': self.custom_voices.get('hausa_female'),
            'igbo': self.custom_voices.get('igbo_female'),
            'yoruba': self.custom_voices.get('yoruba_female'),
        }
        
        return voice_mapping.get(language)
    
    def clone_voice(self, voice_samples: list, voice_name: str, voice_description: str) -> Optional[str]:
        """Clone a voice from audio samples (for creating Nigerian language voices)"""
        try:
            url = f"{self.base_url}/voices/add"
            
            headers = {
                "xi-api-key": self.api_key
            }
            
            files = []
            for i, sample_path in enumerate(voice_samples):
                files.append(('files', (f'sample_{i}.mp3', open(sample_path, 'rb'), 'audio/mpeg')))
            
            data = {
                'name': voice_name,
                'description': voice_description,
                'labels': '{"accent": "nigerian", "age": "adult", "gender": "female"}'
            }
            
            response = requests.post(url, headers=headers, data=data, files=files)
            
            # Close files
            for _, file_tuple in files:
                file_tuple[1].close()
            
            if response.status_code == 200:
                result = response.json()
                return result.get('voice_id')
            else:
                print(f"Voice cloning error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Voice cloning error: {e}")
            return None


class NativeSpeechEngine:
    """Custom engine for Nigerian languages using local TTS models"""
    
    def __init__(self):
        self.model_paths = {
            'hausa': os.getenv('HAUSA_TTS_MODEL_PATH'),
            'igbo': os.getenv('IGBO_TTS_MODEL_PATH'),
            'yoruba': os.getenv('YORUBA_TTS_MODEL_PATH'),
        }
    
    def is_available(self) -> bool:
        return any(path for path in self.model_paths.values() if path and os.path.exists(path))
    
    def synthesize(self, text: str, language: str, voice_style: str = 'neutral') -> Optional[str]:
        """Synthesize using local Nigerian language models"""
        model_path = self.model_paths.get(language)
        if not model_path or not os.path.exists(model_path):
            return None
        
        try:
            # This would integrate with local TTS models
            # Implementation depends on the specific model format
            # Example for a hypothetical local model:
            
            # import your_local_tts_library
            # synthesizer = your_local_tts_library.load_model(model_path)
            # audio_data = synthesizer.synthesize(text)
            
            # For now, return None to indicate not implemented
            return None
            
        except Exception as e:
            print(f"Native TTS error: {e}")
            return None


class AWSPollyEngine:
    """Amazon Polly TTS"""
    
    def __init__(self):
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
    
    def is_available(self) -> bool:
        return bool(self.aws_access_key and self.aws_secret_key)
    
    def synthesize(self, text: str, language: str, voice_style: str = 'neutral') -> Optional[str]:
        """Synthesize speech using AWS Polly"""
        if not self.is_available():
            return None
        
        try:
            polly = boto3.client(
                'polly',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            # Voice selection
            voice_id = self._get_voice_id(language)
            
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                LanguageCode=self._get_language_code(language)
            )
            
            # Save audio
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            output_file.write(response['AudioStream'].read())
            output_file.close()
            
            return output_file.name
            
        except Exception as e:
            print(f"AWS Polly error: {e}")
            return None
    
    def _get_voice_id(self, language: str) -> str:
        """Get voice ID for language"""
        voice_mapping = {
            'english': 'Joanna',  # US English, but clear
            'hausa': 'Joanna',    # Fallback
            'igbo': 'Joanna',     # Fallback
            'yoruba': 'Joanna',   # Fallback
        }
        return voice_mapping.get(language, 'Joanna')
    
    def _get_language_code(self, language: str) -> str:
        """Get language code"""
        code_mapping = {
            'english': 'en-US',
            'hausa': 'en-US',    # Fallback
            'igbo': 'en-US',     # Fallback
            'yoruba': 'en-US',   # Fallback
        }
        return code_mapping.get(language, 'en-US')


class GTTSEngine:
    """Google Text-to-Speech - Free fallback option"""
    
    def is_available(self) -> bool:
        return True  # Always available
    
    def synthesize(self, text: str, language: str, voice_style: str = 'neutral') -> Optional[str]:
        """Synthesize speech using gTTS"""
        try:
            # Language code mapping
            lang_codes = {
                'english': 'en',
                'hausa': 'en',     # Fallback to English
                'igbo': 'en',      # Fallback to English
                'yoruba': 'en',    # Fallback to English
            }
            
            lang_code = lang_codes.get(language, 'en')
            
            tts = gTTS(text=text, lang=lang_code, slow=False)
            
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(output_file.name)
            
            return output_file.name
            
        except Exception as e:
            print(f"gTTS error: {e}")
            return None