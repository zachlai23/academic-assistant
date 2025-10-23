from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from utils.parse_degreeworks import extract_courses_needed, extract_courses_completed
import os
from dotenv import load_dotenv
from agent import agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    user_id: str = "default_user"
    conversation_id: str = "default"
    completed_courses: list[str]
    required: dict = Field(default_factory=dict)

@app.get("/health")
def health_check():
    return {"status": "healthy", "openai_configured": bool(os.getenv("OPENAI_API_KEY"))}

@app.post("/uploadFile/")
async def upload_file(file: UploadFile):
    try:
        upload_dir = "uploads"
        file_path = f"./{upload_dir}/{file.filename}"

        os.makedirs(upload_dir, exist_ok=True)

        with open(file_path, 'wb') as buffer:
            buffer.write(await file.read())

        completed_courses = extract_courses_completed(str(file_path))
        courses_required = extract_courses_needed(str(file_path))

        os.remove(file_path) 

    except Exception as e:
        return {"success": False, "error": str(e)}

    return {
        "success": True,
        "completed_courses": completed_courses,
        "requirements": courses_required
    }

@app.post("/chat")
async def chat_endpoint(chat_message: ChatMessage):
    # Get user message
    message = chat_message.message
    completed_courses = chat_message.completed_courses
    grad_reqs = chat_message.required
    # Call agent
    agent_response = await agent(message, chat_message.conversation_id, completed_courses, grad_reqs)
    # Return response
    return {"response": agent_response}
   
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)