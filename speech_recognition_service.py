import os
import json
import queue
import threading
import time
import logging
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import speech_recognition as sr
from datetime import datetime

logger = logging.getLogger(__name__)

class SpeechRecognitionService:
    def __init__(self, vosk_model_path=None, wake_words=None):
        self.vosk_model_path = vosk_model_path
        self.wake_words = wake_words or ["hey", "jarvis", "billion"]
        self.is_listening = False
        self.is_wake_word_active = False
        self.model = None
        self.recognizer = None
        self.audio_queue = queue.Queue()
        self.callback_function = None
        self.wake_word_callback = None
        self.continuous_listening = False
        
        # Initialize components
        self._init_vosk_model()
        self._init_google_recognizer()
    
    def _init_vosk_model(self):
        """Initialize Vosk model for wake word detection"""
        try:
            if self.vosk_model_path and os.path.exists(self.vosk_model_path):
                self.model = Model(self.vosk_model_path)
                self.recognizer = KaldiRecognizer(self.model, 16000)
                logger.info("Vosk model initialized successfully")
            else:
                logger.warning("Vosk model path not found, wake word detection disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Vosk model: {e}")
    
    def _init_google_recognizer(self):
        """Initialize Google Speech Recognition"""
        try:
            self.google_recognizer = sr.Recognizer()
            # Test microphone
            with sr.Microphone() as source:
                self.google_recognizer.adjust_for_ambient_noise(source, duration=0.5)
            logger.info("Google Speech Recognition initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Speech Recognition: {e}")
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio input"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def start_wake_word_detection(self, callback=None):
        """Start continuous wake word detection"""
        if not self.model:
            logger.error("Vosk model not available for wake word detection")
            return False
        
        self.wake_word_callback = callback
        self.is_wake_word_active = True
        
        def wake_word_loop():
            logger.info("Starting wake word detection...")
            
            with sd.RawInputStream(
                samplerate=16000, 
                blocksize=8000, 
                dtype="int16", 
                channels=1, 
                callback=self._audio_callback
            ):
                while self.is_wake_word_active:
                    try:
                        data = self.audio_queue.get(timeout=1)
                        if self.recognizer.AcceptWaveform(data):
                            result = json.loads(self.recognizer.Result())
                            text = result.get("text", "").lower()
                            
                            if text and any(wake_word in text for wake_word in self.wake_words):
                                logger.info(f"Wake word detected: {text}")
                                if self.wake_word_callback:
                                    self.wake_word_callback(text)
                                
                                # Brief pause after wake word detection
                                time.sleep(0.5)
                    
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"Wake word detection error: {e}")
                        time.sleep(1)
        
        threading.Thread(target=wake_word_loop, daemon=True).start()
        return True
    
    def stop_wake_word_detection(self):
        """Stop wake word detection"""
        self.is_wake_word_active = False
        logger.info("Wake word detection stopped")
    
    def listen_once(self, timeout=5, phrase_time_limit=8):
        """Listen for a single command using Google Speech Recognition"""
        try:
            with sr.Microphone() as source:
                logger.info("Listening for command...")
                self.google_recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.google_recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                
                command = self.google_recognizer.recognize_google(audio)
                logger.info(f"Recognized command: {command}")
                return command.lower()
                
        except sr.WaitTimeoutError:
            logger.warning("Speech recognition timeout")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return None
    
    def start_continuous_listening(self, callback=None):
        """Start continuous speech recognition"""
        if self.continuous_listening:
            return False
        
        self.callback_function = callback
        self.continuous_listening = True
        
        def continuous_loop():
            logger.info("Starting continuous listening...")
            
            while self.continuous_listening:
                try:
                    command = self.listen_once(timeout=2, phrase_time_limit=5)
                    if command and self.callback_function:
                        self.callback_function(command)
                    
                    # Brief pause between listening sessions
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Continuous listening error: {e}")
                    time.sleep(1)
        
        threading.Thread(target=continuous_loop, daemon=True).start()
        return True
    
    def stop_continuous_listening(self):
        """Stop continuous listening"""
        self.continuous_listening = False
        logger.info("Continuous listening stopped")
    
    def get_status(self):
        """Get current status of speech recognition service"""
        return {
            'vosk_available': self.model is not None,
            'google_sr_available': hasattr(self, 'google_recognizer'),
            'wake_word_active': self.is_wake_word_active,
            'continuous_listening': self.continuous_listening,
            'wake_words': self.wake_words
        }

# Global speech service instance
speech_service = None

def init_speech_service(vosk_model_path=None, wake_words=None):
    """Initialize global speech service"""
    global speech_service
    speech_service = SpeechRecognitionService(vosk_model_path, wake_words)
    return speech_service

def get_speech_service():
    """Get global speech service instance"""
    return speech_service
