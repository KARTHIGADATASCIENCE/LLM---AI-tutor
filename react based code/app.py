from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from pathlib import Path
import os
import uvicorn
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
else:
    print("Warning: OPENAI_API_KEY not found in .env file. Using fallback responses.")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend files
frontend_path = Path(__file__).resolve().parent.parent / "frontend"
print(f"Frontend path: {frontend_path}")

@app.get("/")
async def root():
    index_path = frontend_path / "index.html"
    if not index_path.exists():
        print(f"Error: index.html not found at {index_path}")
        return {"error": "index.html not found"}
    print(f"Serving index.html from: {index_path}")
    return FileResponse(index_path)

@app.get("/script.js")
async def serve_script():
    script_path = frontend_path / "script.js"
    if not script_path.exists():
        print(f"Error: script.js not found at {script_path}")
        return {"error": "script.js not found"}
    print(f"Serving script.js from: {script_path}")
    return FileResponse(script_path, media_type="application/javascript")

# Braille map
braille_map = {
    'A': [1], 'B': [1, 2], 'C': [1, 4], 'D': [1, 4, 5], 'E': [1, 5],
    'F': [1, 2, 4], 'G': [1, 2, 4, 5], 'H': [1, 2, 5], 'I': [2, 4],
    'J': [2, 4, 5], 'K': [1, 3], 'L': [1, 2, 3], 'M': [1, 3, 4],
    'N': [1, 3, 4, 5], 'O': [1, 3, 5], 'P': [1, 2, 3, 4], 'Q': [1, 2, 3, 4, 5],
    'R': [1, 2, 3, 5], 'S': [2, 3, 4], 'T': [2, 3, 4, 5], 'U': [1, 3, 6],
    'V': [1, 2, 3, 6], 'W': [2, 4, 5, 6], 'X': [1, 3, 4, 6],
    'Y': [1, 3, 4, 5, 6], 'Z': [1, 3, 5, 6]
}

class BrailleQuery(BaseModel):
    input: str
    targetLetter: str = None

@app.post("/ask")
async def ask(query: BrailleQuery):
    try:
        user_input = query.input
        target_letter = query.targetLetter
        print(f"Received: input='{user_input}', target_letter='{target_letter}'")
        
        # Define dot positions
        dot_positions = {
            1: "top left first dot",
            2: "middle left second dot",
            3: "bottom left third dot",
            4: "top right fourth dot",
            5: "middle right fifth dot",
            6: "bottom right sixth dot"
        }
        
        if client:
            prompt = (
                f"You are a patient, friendly Braille tutor for blind users. The Braille map is: {braille_map}. "
                f"User asked: '{user_input}'. "
                f"Target letter or word: '{target_letter}'. "
                f"Generate a concise, conversational response in simple language. "
                f"For a single letter (e.g., 'A'), describe its dots using these positions: {dot_positions}. "
                f"Example: 'For A, press the top left first dot.' "
                f"For a word (e.g., 'CAT'), describe each letter's dots, e.g., 'C is top left first dot and top right fourth dot, A is top left first dot, T is middle left second dot, bottom left third dot, and middle right fifth dot.' "
                f"For 'What is the 6-dot cell?', say: 'The 6-dot Braille cell has: Dot 1 is top left, Dot 2 is middle left, Dot 3 is bottom left, Dot 4 is top right, Dot 5 is middle right, Dot 6 is bottom right.' "
                f"Vary the phrasing to sound natural and engaging. Keep it under 100 words."
            )
            
            completion = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=100
            )
            response = completion.choices[0].message.content.strip()
        else:
            # Fallback response
            dots = braille_map.get(target_letter, [1]) if target_letter else [1]
            response = f"For {target_letter or 'unknown'}, press {', '.join(f'dot {d}' for d in dots)}."
        
        print(f"Response: {response}")
        return {"response": response}
    except Exception as e:
        error_msg = f"Error in /ask: {str(e)}"
        print(error_msg)
        # Fallback response
        dots = braille_map.get(target_letter, [1]) if target_letter else [1]
        fallback_response = f"For {target_letter or 'unknown'}, press {', '.join(f'dot {d}' for d in dots)}."
        return {"response": fallback_response, "error": error_msg}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)