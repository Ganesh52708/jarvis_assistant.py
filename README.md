# JARVIS AI Assistant

A sophisticated AI assistant with a futuristic JARVIS-style interface, combining voice recognition, AI chat, and system control capabilities.

## Features

- **Voice Recognition**: Activate with "Hey JARVIS" wake word
- **AI Chat**: Powered by OpenAI/OpenRouter API
- **System Control**: File management, browser control, keyboard shortcuts
- **Futuristic UI**: Arc reactor interface with animations
- **Text-to-Speech**: British-accented voice responses
- **Web Interface**: Accessible through browser

## Setup

1. Install Python dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Download Vosk model:
   - Download from: https://alphacephei.com/vosk/models
   - Extract to: `vosk-model-small-en-us-0.15/`

3. Configure API key:
   - Update `OPENROUTER_API_KEY` in `app.py`

4. Run the application:
\`\`\`bash
python app.py
\`\`\`

5. Open browser to: http://localhost:5000

## Usage

- Click the arc reactor to activate/deactivate
- Use voice commands or type in chat
- Click sidebar apps for quick actions
- Say "Hey JARVIS" to activate voice control

## Commands

- "Open Google/YouTube"
- "Play [song] on YouTube"
- "Open file manager"
- "Close [application]"
- Keyboard shortcuts (copy, paste, etc.)
- General conversation with AI

## Requirements

- Python 3.8+
- Microphone for voice input
- Internet connection for AI responses
