# Braille Tutor API

![Braille System Visualization](https://via.placeholder.com/150x100?text=Braille) *(Replace with actual Braille visualization)*

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [API Endpoints](#api-endpoints)
- [WebSocket Protocol](#websocket-protocol)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Deployment](#deployment)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

## Introduction

The Braille Tutor API is a FastAPI-powered backend service designed to support Braille learning applications. It provides:

- Structured Braille lessons across three difficulty levels
- Real-time AI tutoring via WebSocket
- User progress tracking
- Text-to-speech conversion for accessibility

## Features

### 📚 Lesson Management
- **Beginner Level**: Complete Braille alphabet (A-Z) with dot patterns
- **Intermediate Level**: Contractions, punctuation, and numbers
- **Advanced Level**: Literary, mathematical, and musical Braille

### 🤖 AI-Powered Tutoring
- GPT-4 powered conversational tutor
- Level-specific system prompts
- Persistent conversation context
- WebSocket-based real-time interaction

### 📊 Progress Tracking
- Lesson completion tracking
- XP-based achievement system
- Simple in-memory storage (can be extended to database)

### ♿ Accessibility Features
- Text-to-speech conversion via gTTS
- CORS-enabled for cross-platform access
- Error handling for all endpoints

## API Endpoints

### REST Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/lessons` | GET | Get lessons by level | `level` (comma-separated) |
| `/progress` | GET | Get user progress | `user_id` |
| `/progress` | POST | Update user progress | JSON body (see below) |
| `/tts` | GET | Convert text to speech | `text` |

### WebSocket Endpoint
- `ws://<host>/ws/tutor` - Real-time AI tutoring interface

## WebSocket Protocol

### Connection Flow
1. Client connects to `ws://<host>/ws/tutor`
2. Server accepts connection
3. Client sends messages in JSON format:
   ```json
   {
     "user_id": "unique_user_id",
     "message": "Your question",
     "level": "Beginner/Intermediate/Advanced"
   }

### Server responds with:

    '''json
    {
        "response": "AI-generated answer"
    }
### Error Handling
    Automatic reconnection on disconnect

## Error messages returned in the same JSON format

## Installation
Prerequisites
Python 3.8+

OpenAI API key

Port 8000 available

## Steps
Clone the repository

Create and activate virtual environment:

bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
Install dependencies:

bash
pip install fastapi uvicorn openai gtts python-dotenv
Set up environment variables:

bash
echo "OPENAI_API_KEY=your_api_key" > .env
Run the server:

bash
uvicorn main:app --reload
Configuration
Environment Variables
OPENAI_API_KEY: Required for AI tutoring functionality

PORT: Optional (default: 8000)

## CORS Settings
Currently configured to allow all origins (for development):

python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
## Usage Examples
Fetching Lessons
bash
curl "http://localhost:8000/lessons?level=Beginner,Advanced"
Updating Progress
bash
curl -X POST "http://localhost:8000/progress" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123", "lesson_id": 5, "status": "completed", "xp": 10}'
Text-to-Speech
html
<audio controls src="http://localhost:8000/tts?text=Hello%20Braille%20learner">
  Your browser does not support audio
</audio>
WebSocket Client (JavaScript)
javascript
const socket = new WebSocket("ws://localhost:8000/ws/tutor");

socket.onmessage = (event) => {
  console.log("Tutor:", JSON.parse(event.data).response);
};

socket.send(JSON.stringify({
  user_id: "user_123",
  message: "Explain Braille letter A",
  level: "Beginner"
}));

### Architecture
Key Components
FastAPI Application: Main server instance

WebSocket Handler: Manages real-time tutoring sessions

OpenAI Integration: GPT-4 powered responses

gTTS Service: Text-to-speech conversion

Lesson Data: Pre-defined Braille patterns