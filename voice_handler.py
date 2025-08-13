# voice_handler.py
import speech_recognition as sr
import whisper
from gtts import gTTS
import pygame
import io
import tempfile
import os
from typing import Optional, Tuple
import threading
import time
from multilingual_handler import MultilingualHandler

class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.whisper_model = whisper.load_model("base")
        self.multilingual = MultilingualHandler()
        pygame.mixer.init()
        
        # Calibrate microphone
        with self.microphone as source:
            print("Calibrating microphone...")
            self.recognizer.adjust_for_ambient_noise(source)
            print("Microphone calibrated!")
    
    def listen_for_wake_word(self, wake_word: str = "hey farmdepot") -> bool:
        """Listen for wake word continuously"""
        try:
            with self.microphone as source:
                print(f"Listening for wake word: '{wake_word}'...")
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                
            text = self.recognize_speech(audio)
            if text and wake_word.lower() in text.lower():
                print(f"Wake word detected: {text}")
                return True
            return False
        except sr.WaitTimeoutError:
            return False
        except Exception as e:
            print(f"Error listening for wake word: {e}")
            return False
    
    def listen_for_command(self, timeout: int = 10) -> Optional[dict]:
        """Listen for voice command after wake word and return multilingual analysis"""
        try:
            with self.microphone as source:
                print("Listening for command...")
                # Play a beep to indicate listening
                self.play_beep()
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
            command_text = self.recognize_speech(audio)
            if command_text:
                print(f"Command received: {command_text}")
                # Parse multilingual command
                parsed_command = self.multilingual.parse_multilingual_command(command_text)
                return parsed_command
            else:
                print("No command recognized")
                return None
        except sr.WaitTimeoutError:
            print("Listening timeout")
            return None
        except Exception as e:
            print(f"Error listening for command: {e}")
            return None
    
    def recognize_speech(self, audio) -> Optional[str]:
        """Recognize speech using both SpeechRecognition and Whisper"""
        try:
            # First try with Google Speech Recognition (faster)
            try:
                text = self.recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                pass
            
            # Fallback to Whisper (more accurate, works offline)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio.get_wav_data())
                tmp_file.flush()
                
                result = self.whisper_model.transcribe(tmp_file.name)
                os.unlink(tmp_file.name)
                
                return result["text"].strip() if result["text"].strip() else None
                
        except Exception as e:
            print(f"Speech recognition error: {e}")
            return None
    
    def text_to_speech(self, text: str, language: str = None) -> bool:
        """Convert text to speech with multilingual support"""
        try:
            # Use multilingual TTS generation
            tts = self.multilingual.generate_multilingual_tts(text, language)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tts.save(tmp_file.name)
                
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                os.unlink(tmp_file.name)
                return True
                
        except Exception as e:
            print(f"Text-to-speech error: {e}")
            return False
    
    def play_beep(self, frequency: int = 1000, duration: float = 0.3):
        """Play a simple beep sound"""
        try:
            import numpy as np
            sample_rate = 22050
            frames = int(duration * sample_rate)
            arr = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
            arr = (arr * 32767).astype(np.int16)
            
            # Convert to stereo
            stereo_arr = np.array([arr, arr]).T
            
            sound = pygame.sndarray.make_sound(stereo_arr)
            sound.play()
            time.sleep(duration)
        except Exception as e:
            print(f"Beep error: {e}")
    
    def continuous_listening(self, callback_function, wake_words: dict = None):
        """Continuous listening loop with multilingual wake words"""
        if wake_words is None:
            wake_words = {
                'english': "hey farmdepot",
                'hausa': "kai farmdepot",
                'igbo': "ndewo farmdepot", 
                'yoruba': "eku farmdepot"
            }
        
        print("Starting continuous listening with multilingual support...")
        while True:
            try:
                # Listen for any wake word
                wake_detected = False
                detected_language = 'english'
                
                for lang, wake_word in wake_words.items():
                    if self.listen_for_wake_word(wake_word):
                        wake_detected = True
                        detected_language = lang
                        self.multilingual.current_language = lang
                        break
                
                if wake_detected:
                    command_data = self.listen_for_command()
                    if command_data:
                        # Use detected language from command or wake word
                        response_language = command_data.get('detected_language', detected_language)
                        response = callback_function(command_data)
                        if response:
                            self.text_to_speech(response, response_language)
                    else:
                        # Respond in detected language
                        error_msg = self.multilingual.get_response_text('not_understood', detected_language)
                        self.text_to_speech(error_msg, detected_language)
                        
                time.sleep(0.5)  # Small delay to prevent excessive CPU usage
            except KeyboardInterrupt:
                print("Stopping continuous listening...")
                break
            except Exception as e:
                print(f"Error in continuous listening: {e}")
                time.sleep(1)

class VoiceWebInterface:
    """Web interface for voice interactions with multilingual support"""
    def __init__(self, voice_handler: VoiceHandler):
        self.voice_handler = voice_handler
        self.multilingual = voice_handler.multilingual
    
    def process_voice_input(self, audio_file_path: str) -> dict:
        """Process uploaded voice file with multilingual analysis"""
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.voice_handler.recognizer.record(source)
            
            text = self.voice_handler.recognize_speech(audio)
            if text:
                # Parse multilingual command
                parsed_command = self.multilingual.parse_multilingual_command(text)
                return {
                    'success': True,
                    'text': text,
                    'parsed_command': parsed_command
                }
            else:
                return {
                    'success': False,
                    'error': "Could not understand the audio"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error processing voice input: {str(e)}"
            }
    
    def generate_voice_response(self, text: str, language: str = None) -> str:
        """Generate voice response file with multilingual TTS"""
        try:
            # Use multilingual TTS
            tts = self.multilingual.generate_multilingual_tts(text, language)
            
            # Create temporary file in web-accessible directory
            output_dir = "static/voice_responses"
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = int(time.time())
            output_file = f"{output_dir}/response_{timestamp}.mp3"
            
            tts.save(output_file)
            return output_file
        except Exception as e:
            print(f"Error generating voice response: {e}")
            return None