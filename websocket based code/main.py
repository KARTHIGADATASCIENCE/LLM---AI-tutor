from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
from openai import OpenAI
import os
import uvicorn
from gtts import gTTS
import tempfile

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# Allow all origins for Flutter mobile testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LESSONS = {
    "Beginner": [
        {"id": 1, "title": "Learn A", "dots": [1]},
        {"id": 2, "title": "Learn B", "dots": [1, 2]},
        {"id": 3, "title": "Learn C", "dots": [1, 4]},
        {"id": 4, "title": "Learn D", "dots": [1, 4, 5]},
        {"id": 5, "title": "Learn E", "dots": [1, 5]},
        {"id": 6, "title": "Learn F", "dots": [1, 2, 4]},
        {"id": 7, "title": "Learn G", "dots": [1, 2, 4, 5]},
        {"id": 8, "title": "Learn H", "dots": [1, 2, 5]},
        {"id": 9, "title": "Learn I", "dots": [2, 4]},
        {"id": 10, "title": "Learn J", "dots": [2, 4, 5]},
        {"id": 11, "title": "Learn K", "dots": [1, 3]},
        {"id": 12, "title": "Learn L", "dots": [1, 2, 3]},
        {"id": 13, "title": "Learn M", "dots": [1, 3, 4]},
        {"id": 14, "title": "Learn N", "dots": [1, 3, 4, 5]},
        {"id": 15, "title": "Learn O", "dots": [1, 3, 5]},
        {"id": 16, "title": "Learn P", "dots": [1, 2, 3, 4]},
        {"id": 17, "title": "Learn Q", "dots": [1, 2, 3, 4, 5]},
        {"id": 18, "title": "Learn R", "dots": [1, 2, 3, 5]},
        {"id": 19, "title": "Learn S", "dots": [2, 3, 4]},
        {"id": 20, "title": "Learn T", "dots": [2, 3, 4, 5]},
        {"id": 21, "title": "Learn U", "dots": [1, 3, 6]},
        {"id": 22, "title": "Learn V", "dots": [1, 2, 3, 6]},
        {"id": 23, "title": "Learn W", "dots": [2, 4, 5, 6]},
        {"id": 24, "title": "Learn X", "dots": [1, 3, 4, 6]},
        {"id": 25, "title": "Learn Y", "dots": [1, 3, 4, 5, 6]},
        {"id": 26, "title": "Learn Z", "dots": [1, 3, 5, 6]}
    ],
    "Intermediate": [
        {"id": 101, "title": "Learn Contractions", "dots": [], "description": "Learn common Braille contractions like 'and', 'for', 'the'."},
        {"id": 102, "title": "Learn Punctuation", "dots": [], "description": "Learn Braille punctuation marks like comma, period, question mark."},
        {"id": 103, "title": "Learn Numbers", "dots": [], "description": "Learn Braille numeric characters."}
    ],
    "Advanced": [
        {"id": 201, "title": "Learn Literary Braille", "dots": [], "description": "Advanced literary Braille symbols and formatting."},
        {"id": 202, "title": "Learn Mathematical Braille", "dots": [], "description": "Braille notation for math and science symbols."},
        {"id": 203, "title": "Learn Music Braille", "dots": [], "description": "Braille notation for musical scores."}
    ]
}

PROGRESS: Dict[str, Dict] = {}  # user_id -> progress

class TutorMessage(BaseModel):
    user_id: str
    message: str
    level: str

class ProgressUpdate(BaseModel):
    user_id: str
    lesson_id: int
    status: str
    xp: int

# System prompts for different levels
SYSTEM_PROMPTS = {
    "Beginner": "You are a Braille tutor teaching basic Braille alphabet for visually impaired learners.",
    "Intermediate": "You are a Braille tutor teaching contractions, punctuation, and numbers in Braille.",
    "Advanced": "You are a Braille tutor teaching literary, mathematical, and music Braille notation."
}

@app.websocket("/ws/tutor")
async def websocket_tutor(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    conversation_history = []
    system_message_added = False

    try:
        while True:
            data = await websocket.receive_json()
            user_id = data.get("user_id")
            message = data.get("message")
            level = data.get("level", "Beginner")

            if not system_message_added:
                # Add system prompt once per connection based on level
                system_prompt = SYSTEM_PROMPTS.get(level, SYSTEM_PROMPTS["Beginner"])
                conversation_history.append({"role": "system", "content": system_prompt})
                system_message_added = True

            conversation_history.append({"role": "user", "content": message})

            response = client.chat.completions.create(
                model="gpt-4",
                messages=conversation_history
            )

            reply = response.choices[0].message.content
            conversation_history.append({"role": "assistant", "content": reply})

            await websocket.send_json({"response": reply})

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        await websocket.send_json({"response": f"Error: {str(e)}"})

@app.get("/lessons")
def get_lessons(level: str = "Beginner,Intermediate,Advanced"):
    levels = level.split(",")
    return {lvl: LESSONS.get(lvl, []) for lvl in levels}

@app.post("/progress")
def save_progress(update: ProgressUpdate):
    user = PROGRESS.setdefault(update.user_id, {"completed_lessons": [], "xp": 0})
    if update.status == "completed" and update.lesson_id not in user["completed_lessons"]:
        user["completed_lessons"].append(update.lesson_id)
        user["xp"] += update.xp
    return {"status": "success"}

@app.get("/progress")
def get_progress(user_id: str):
    return PROGRESS.get(user_id, {"completed_lessons": [], "xp": 0})

@app.get("/tts")
def get_tts(text: str):
    try:
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tts.save(tmp.name)
            with open(tmp.name, "rb") as f:
                audio = f.read()
        return Response(content=audio, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
