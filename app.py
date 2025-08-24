import os
import json
import queue
import subprocess
import webbrowser
import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pyttsx3
import speech_recognition as sr
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import pyautogui
import openai
import time
import sys
import pygetwindow as gw
import numpy as np
import cv2
import mss
import base64
from PIL import ImageGrab
import threading
import logging
import ai_assistant 
from functools import wraps
from speech_recognition_service import init_speech_service, get_speech_service

# ========== CONFIG ==========
OPENROUTER_API_KEY = "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"
VOSK_MODEL_PATH = r"C:\Users\Ganesh Yadav\OneDrive\Desktop\jarvis_assistant.py\vosk-model-small-en-us-0.15"

WAKE_WORDS = ["hey", "jarvis", "billion"]
EXIT_COMMANDS = ["shutdown", "terminate", "exit", "goodbye"]

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
is_listening = False
speech_thread = None
tts_engine = None
conversation_history = []
speech_service = None

speech_queue = queue.Queue()
speech_lock = threading.Lock()
speech_worker_thread = None
speech_worker_running = False

def init_tts_engine():
    """Initialize text-to-speech engine"""
    global tts_engine
    try:
        tts_engine = pyttsx3.init()
        tts_engine.setProperty('rate', 150)
        voices = tts_engine.getProperty('voices')
        
        # Try to find a British male voice
        for voice in voices:
            if "male" in voice.name.lower() and ("uk" in voice.id.lower() or "english_rp" in voice.id.lower()):
                tts_engine.setProperty('voice', voice.id)
                break
        
        logger.info("TTS engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize TTS engine: {e}")
        tts_engine = None

def speech_worker():
    """Worker thread to handle speech synthesis queue"""
    global speech_worker_running, tts_engine
    
    while speech_worker_running:
        try:
            # Get text from queue with timeout
            text = speech_queue.get(timeout=1.0)
            
            if text is None:  # Shutdown signal
                break
                
            # Use lock to ensure thread-safe TTS operation
            with speech_lock:
                if tts_engine:
                    try:
                        tts_engine.say(text)
                        tts_engine.runAndWait()
                        logger.info(f"Spoke: {text[:50]}...")
                    except Exception as e:
                        logger.error(f"TTS error: {e}")
                        # Reinitialize TTS engine if it fails
                        init_tts_engine()
                else:
                    logger.warning("TTS engine not available")
            
            speech_queue.task_done()
            
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Speech worker error: {e}")

def start_speech_worker():
    """Start the speech worker thread"""
    global speech_worker_thread, speech_worker_running
    
    if speech_worker_thread is None or not speech_worker_thread.is_alive():
        speech_worker_running = True
        speech_worker_thread = threading.Thread(target=speech_worker, daemon=True)
        speech_worker_thread.start()
        logger.info("Speech worker thread started")

def stop_speech_worker():
    """Stop the speech worker thread"""
    global speech_worker_running
    
    speech_worker_running = False
    speech_queue.put(None)  # Shutdown signal

def handle_api_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {f.__name__}: {e}")
            return jsonify({
                'success': False, 
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat()
            }), 500
    return decorated_function

def speak(text):
    """Add text to speech queue for thread-safe processing"""
    try:
        if not speech_worker_running:
            start_speech_worker()
        
        # Add text to queue
        speech_queue.put(text)
        logger.info(f"Added to speech queue: {text[:50]}...")
        
    except Exception as e:
        logger.error(f"Speech queue error: {e}")

# Enhanced text-to-speech function with better error handling
def speak(text):
    global tts_engine
    try:
        if tts_engine is None:
            init_tts_engine()
        
        if tts_engine:
            tts_engine.say(text)
            tts_engine.runAndWait()
            logger.info(f"Spoke: {text[:50]}...")
        else:
            logger.warning("TTS engine not available")
    except Exception as e:
        logger.error(f"Speech error: {e}")

# Enhanced AI function with conversation history and better error handling
openai.api_key = OPENROUTER_API_KEY
openai.api_base = "https://openrouter.ai/api/v1"

def ask_billion(message, include_history=True):
    global conversation_history
    
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are JARVIS, an intelligent British-accented AI assistant inspired by Tony Stark's AI. "
                    "You are sophisticated, respectful, and highly capable. Address the user as 'sir' or 'madam' appropriately. "
                    "Be concise but informative. You can control computer systems, browse the web, play music, "
                    "manage files, and engage in intelligent conversation. Always maintain a professional yet friendly demeanor."
                )
            }
        ]
        
        if include_history and conversation_history:
            messages.extend(conversation_history[-10:])  # Last 10 messages
        
        messages.append({"role": "user", "content": message})
        
        response = openai.ChatCompletion.create(
            model="mistralai/mistral-7b-instruct",
            messages=messages,
            temperature=0.7,
            top_p=0.9,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message["content"]
        
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        logger.info(f"AI response generated for: {message[:30]}...")
        return ai_response
        
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "I apologize, sir. I'm experiencing some technical difficulties at the moment."

# Get appropriate greeting based on time
def time_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning, sir."
    elif hour < 17:
        return "Good afternoon, sir."
    else:
        return "Good evening, sir."

# Enhanced browser control with better URL handling
def open_browser_and_search(site, query=""):
    try:
        if "youtube" in site.lower():
            if query:
                url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            else:
                url = "https://www.youtube.com"
        elif "google" in site.lower():
            if query:
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            else:
                url = "https://www.google.com"
        else:
            url = f"https://www.google.com/search?q={site.replace(' ', '+')}"
        
        webbrowser.open(url)
        logger.info(f"Opened browser: {url}")
        return True
    except Exception as e:
        logger.error(f"Browser error: {e}")
        return False

# Play song on YouTube with enhanced search
def play_song_on_youtube(song_name):
    try:
        search_query = song_name.replace(' ', '+')
        url = f"https://www.youtube.com/results?search_query={search_query}"
        webbrowser.open(url)
        logger.info(f"Playing song: {song_name}")
        return True
    except Exception as e:
        logger.error(f"YouTube error: {e}")
        return False

# Enhanced file manager with optional path
def open_file_manager(path=""):
    try:
        if path:
            subprocess.Popen(f'explorer "{path}"')
        else:
            subprocess.Popen("explorer")
        logger.info(f"Opened file manager: {path or 'default'}")
        return True
    except Exception as e:
        logger.error(f"File manager error: {e}")
        return False

# Enhanced keyboard command handling
def handle_keyboard_commands(command):
    actions = {
        "select all": "ctrl+a",
        "copy": "ctrl+c",
        "cut": "ctrl+x",
        "paste": "ctrl+v",
        "delete": "delete",
        "enter": "enter",
        "save": "ctrl+s",
        "undo": "ctrl+z",
        "redo": "ctrl+y",
        "close window": "alt+f4",
        "new tab": "ctrl+t",
        "close tab": "ctrl+w",
        "refresh": "f5",
        "find": "ctrl+f"
    }

    for phrase, keys in actions.items():
        if phrase in command.lower():
            try:
                if "+" in keys:
                    pyautogui.hotkey(*keys.split("+"))
                else:
                    pyautogui.press(keys)
                logger.info(f"Executed keyboard command: {phrase}")
                return True
            except Exception as e:
                logger.error(f"Keyboard command error: {e}")
                return False
    return False

# Enhanced window closing with better app detection
def close_window(app_name):
    try:
        all_windows = gw.getAllTitles()
        closed_windows = []
        
        for title in all_windows:
            if app_name.lower() in title.lower() and title.strip():
                try:
                    win = gw.getWindowsWithTitle(title)[0]
                    win.close()
                    closed_windows.append(title)
                    logger.info(f"Closed window: {title}")
                except:
                    continue
        
        return len(closed_windows) > 0
    except Exception as e:
        logger.error(f"Window closing error: {e}")
        return False

# Handle wake word detection
def handle_wake_word(text):
    logger.info(f"Wake word detected: {text}")
    # You can add additional wake word handling logic here

# Handle voice command from continuous listening
def handle_voice_command(command):
    logger.info(f"Voice command received: {command}")
    # Process the command through the existing command handler
    # This would typically be called from the frontend

# Serve the main JARVIS interface
@app.route('/')
def home():
    return render_template('jarvis-interface.html')

# Enhanced API endpoint for text-to-speech
@app.route('/api/speak', methods=['POST'])
@handle_api_errors
def api_speak():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'success': False, 'error': 'No text provided'})
    
    speak(text)
    
    return jsonify({
        'success': True, 
        'message': 'Speech queued',
        'text': text[:100] + '...' if len(text) > 100 else text,
        'queue_size': speech_queue.qsize()
    })

# Enhanced API endpoint for speech recognition
@app.route('/api/listen', methods=['POST'])
@handle_api_errors
def api_listen():
    data = request.get_json()
    listen_type = data.get('type', 'once')  # 'once', 'continuous', 'wake_word'
    
    if not speech_service:
        return jsonify({
            'success': False, 
            'error': 'Speech recognition service not available'
        })
    
    if listen_type == 'once':
        command = speech_service.listen_once()
        if command:
            return jsonify({
                'success': True, 
                'command': command,
                'timestamp': datetime.datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'No speech detected or recognition failed'
            })
    
    elif listen_type == 'start_continuous':
        success = speech_service.start_continuous_listening(handle_voice_command)
        return jsonify({
            'success': success,
            'message': 'Continuous listening started' if success else 'Failed to start continuous listening'
        })
    
    elif listen_type == 'stop_continuous':
        speech_service.stop_continuous_listening()
        return jsonify({
            'success': True,
            'message': 'Continuous listening stopped'
        })
    
    elif listen_type == 'start_wake_word':
        success = speech_service.start_wake_word_detection(handle_wake_word)
        return jsonify({
            'success': success,
            'message': 'Wake word detection started' if success else 'Wake word detection not available'
        })
    
    elif listen_type == 'stop_wake_word':
        speech_service.stop_wake_word_detection()
        return jsonify({
            'success': True,
            'message': 'Wake word detection stopped'
        })
    
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid listen type'
        })

# Enhanced API endpoint for AI chat with conversation history
@app.route('/api/chat', methods=['POST'])
@handle_api_errors
def api_chat():
    data = request.get_json()
    message = data.get('message', '')
    include_history = data.get('include_history', True)
    
    if not message:
        return jsonify({'success': False, 'error': 'No message provided'})
    
    response = ask_billion(message, include_history)
    
    return jsonify({
        'success': True, 
        'response': response,
        'timestamp': datetime.datetime.now().isoformat(),
        'conversation_length': len(conversation_history)
    })

# Enhanced API endpoint for executing system commands
@app.route('/api/command', methods=['POST'])
@handle_api_errors
def api_command():
    data = request.get_json()
    command = data.get('command', '').lower().strip()
    
    if not command:
        return jsonify({'success': False, 'error': 'No command provided'})
    
    logger.info(f"Processing command: {command}")
    
    if any(exit_cmd in command for exit_cmd in EXIT_COMMANDS):
        return jsonify({
            'success': True, 
            'action': 'shutdown', 
            'message': 'Shutting down systems, sir. Goodbye.'
        })
    
    elif "open google" in command:
        query = command.replace("open google", "").strip()
        if open_browser_and_search("google", query):
            msg = f"Opening Google{' and searching for ' + query if query else ''}, sir."
            return jsonify({'success': True, 'action': 'browser', 'message': msg})
    
    elif "open youtube" in command:
        query = command.replace("open youtube", "").strip()
        if open_browser_and_search("youtube", query):
            msg = f"Opening YouTube{' and searching for ' + query if query else ''}, sir."
            return jsonify({'success': True, 'action': 'browser', 'message': msg})
    
    elif "play" in command and ("youtube" in command or "music" in command):
        song = command.replace("play", "").replace("on youtube", "").replace("music", "").strip()
        if song and play_song_on_youtube(song):
            return jsonify({
                'success': True, 
                'action': 'music', 
                'message': f'Playing "{song}" on YouTube, sir.'
            })
    
    elif "open file manager" in command or "open explorer" in command:
        if open_file_manager():
            return jsonify({
                'success': True, 
                'action': 'file_manager', 
                'message': 'Opening file manager, sir.'
            })
    
    elif "close" in command and "window" in command:
        app_name = command.replace("close", "").replace("window", "").strip()
        if app_name and close_window(app_name):
            return jsonify({
                'success': True, 
                'action': 'close_app', 
                'message': f'Closed {app_name}, sir.'
            })
    
    elif handle_keyboard_commands(command):
        return jsonify({
            'success': True, 
            'action': 'keyboard', 
            'message': 'Keyboard command executed, sir.'
        })
    
    elif any(wake in command for wake in WAKE_WORDS):
        return jsonify({
            'success': True, 
            'action': 'wake', 
            'message': 'Yes sir, how may I assist you?'
        })
    
    else:
        response = ask_billion(command)
        return jsonify({
            'success': True, 
            'action': 'chat', 
            'response': response,
            'original_command': command
        })

# Get speech recognition service status
@app.route('/api/speech-status', methods=['GET'])
@handle_api_errors
def api_speech_status():
    if not speech_service:
        return jsonify({
            'success': False,
            'error': 'Speech service not initialized'
        })
    
    status = speech_service.get_status()
    return jsonify({
        'success': True,
        'speech_status': status,
        'timestamp': datetime.datetime.now().isoformat()
    })

# Enhanced API endpoint for comprehensive system status
@app.route('/api/status', methods=['GET'])
@handle_api_errors
def api_status():
    current_time = datetime.datetime.now().strftime("%I : %M : %S %p")
    greeting = time_greeting()
    
    tts_status = "ONLINE" if tts_engine else "OFFLINE"
    
    speech_status = "OFFLINE"
    if speech_service:
        status = speech_service.get_status()
        if status['google_sr_available']:
            speech_status = "READY"
            if status['continuous_listening']:
                speech_status = "LISTENING"
            elif status['wake_word_active']:
                speech_status = "WAKE_WORD_ACTIVE"
    
    return jsonify({
        'success': True,
        'time': current_time,
        'greeting': greeting,
        'status': 'online',
        'components': {
            'tts': tts_status,
            'speech_recognition': speech_status,
            'ai': 'ONLINE',
            'system_control': 'ACTIVE'
        },
        'conversation_history_length': len(conversation_history),
        'uptime': datetime.datetime.now().isoformat()
    })

# Clear conversation history
@app.route('/api/clear-history', methods=['POST'])
@handle_api_errors
def api_clear_history():
    global conversation_history
    conversation_history = []
    
    return jsonify({
        'success': True,
        'message': 'Conversation history cleared, sir.',
        'timestamp': datetime.datetime.now().isoformat()
    })

# Get conversation history
@app.route('/api/history', methods=['GET'])
@handle_api_errors
def api_get_history():
    return jsonify({
        'success': True,
        'history': conversation_history,
        'length': len(conversation_history),
        'timestamp': datetime.datetime.now().isoformat()
    })

# Get detailed system information
@app.route('/api/system-info', methods=['GET'])
@handle_api_errors
def api_system_info():
    import platform
    import psutil
    
    try:
        system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            }
        }
    except:
        system_info = {'error': 'Could not retrieve system information'}
    
    return jsonify({
        'success': True,
        'system_info': system_info,
        'jarvis_status': {
            'tts_engine': tts_engine is not None,
            'conversation_history': len(conversation_history),
            'uptime': datetime.datetime.now().isoformat()
        }
    })

if __name__ == "__main__":
    print("🤖 JARVIS AI Assistant Starting...")
    print(f"🕐 {time_greeting()}")
    print("🌐 Web interface will be available at http://localhost:5000")
    
    init_tts_engine()
    start_speech_worker()  # Start speech worker on startup
    
    speech_service = init_speech_service(VOSK_MODEL_PATH, WAKE_WORDS)
    logger.info("Speech recognition service initialized")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
    finally:
        stop_speech_worker()
        logger.info("JARVIS AI Assistant shutting down...")
