# JARVIS AI Assistant - Startup Guide

## Quick Start

1. **Install Dependencies**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

2. **Configure API Key**
   - Edit `app.py` and update `OPENROUTER_API_KEY` with your OpenRouter API key
   - Or set as environment variable: `export OPENROUTER_API_KEY="your-key-here"`

3. **Optional: Download Vosk Model for Wake Word Detection**
   - Download from: https://alphacephei.com/vosk/models
   - Extract to the path specified in `VOSK_MODEL_PATH` in `app.py`
   - Or update the path to match your model location

4. **Run the Application**
   \`\`\`bash
   python app.py
   \`\`\`

5. **Open Browser**
   - Navigate to: http://localhost:5000
   - Allow microphone permissions when prompted

## Features Overview

### Voice Control
- **Single Command**: Click microphone button or use Ctrl+Space
- **Continuous Listening**: Use sidebar "Voice Control" button
- **Wake Word Detection**: Use sidebar "Wake Word" button (requires Vosk model)

### Available Commands
- **System Control**: "Open Google", "Open YouTube", "Open file manager"
- **Music**: "Play [song name] on YouTube"
- **Keyboard**: "Copy", "Paste", "Save", "Close window"
- **Conversation**: Ask any question or have a chat
- **System**: "Shutdown" to deactivate

### Interface Elements
- **Arc Reactor**: Click to activate/deactivate system
- **Chat Panel**: Type messages or view conversation history
- **Status Panel**: Monitor system components
- **Sidebar Apps**: Quick access to functions

## Troubleshooting

### Voice Recognition Issues
- Ensure microphone permissions are granted
- Check browser compatibility (Chrome/Edge recommended)
- Verify microphone is working in other applications

### Connection Issues
- Check if Flask server is running on port 5000
- Verify no firewall blocking localhost connections
- Look for error messages in browser console (F12)

### API Issues
- Verify OpenRouter API key is valid
- Check internet connection for AI responses
- Monitor Flask console for error messages

### Performance Issues
- Close unnecessary browser tabs
- Restart the Flask application
- Check system resources (CPU/Memory)

## Configuration Options

### Environment Variables
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `VOSK_MODEL_PATH`: Path to Vosk model directory
- `FLASK_DEBUG`: Set to "1" for debug mode

### Customization
- Modify `WAKE_WORDS` in `app.py` to change wake word triggers
- Adjust `conversation_history` limit for memory management
- Update voice settings in TTS engine initialization

## Security Notes
- Keep your API key secure and never commit it to version control
- The application runs on localhost by default for security
- Microphone access is required for voice features

## Support
- Check Flask console output for detailed error messages
- Browser developer tools (F12) show client-side errors
- Ensure all dependencies are properly installed
