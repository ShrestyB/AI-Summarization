import os
import uvicorn
import google.generativeai as genai
import anthropic
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.templating import Jinja2Templates
from pypdf import PdfReader
from dotenv import load_dotenv
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
import datetime

processing_status = {"current_stage": "", "message": ""}

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

DEFAULT_GEMINI_MODEL = "gemini-pro"
DEFAULT_CLAUDE_MODEL = "claude-3-opus-20240229"

genai.configure(api_key=GEMINI_API_KEY)
anthropic_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renders the upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get('/status')
async def status_stream(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            if processing_status["current_stage"]:
                yield {
                    "data": json.dumps({
                        "stage": processing_status["current_stage"],
                        "message": processing_status["message"],
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                }
            await asyncio.sleep(0.1)
    return EventSourceResponse(event_generator())

@app.post("/summarize")
async def summarize_pdf(
    request: Request,
    file: UploadFile = File(...),
    model_choice: str = Form("claude"),
    custom_prompt: str = Form(None)
):
    """Handles file upload and dynamic streaming of summary chunks."""
    try:
        reader = PdfReader(file.file)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        if not text:
            return JSONResponse(
                content={
                    "status": "error",
                    "stage": "extraction",
                    "summary": "No extractable text found in PDF.",
                    "message": "PDF extraction failed"
                }
            )
        
        async def generate_response():
            yield json.dumps({
                "status": "incoming",
                "stage": "processing",
                "message": "Extracting text from PDF..."
            }) + "\n"
            await asyncio.sleep(0.5)
            
            yield json.dumps({
                "status": "incoming",
                "stage": "initialization",
                "message": "Initializing model..."
            }) + "\n"
            await asyncio.sleep(0.5)
            
          
            if model_choice == "gemini" and GEMINI_API_KEY:
                final_prompt = (f"{custom_prompt}:\n{text}"
                                if custom_prompt
                                else f"Summarize this text concisely:\n{text}")
                model_instance = genai.GenerativeModel(DEFAULT_GEMINI_MODEL)
                result = model_instance.generate_content(final_prompt)
                summary = result.text if hasattr(result, "text") else "No summary generated."
            elif model_choice == "claude" and CLAUDE_API_KEY:
                final_prompt = (f"\n\nHuman: {custom_prompt if custom_prompt else 'Summarize this text concisely:'}:\n{text}\n\nAssistant:")
                response = anthropic_client.messages.create(
                    model=DEFAULT_CLAUDE_MODEL,
                    max_tokens=500,
                    messages=[{"role": "user", "content": final_prompt}]
                )
                summary = response.content[0].text if response.content else "No summary generated."
            else:
                summary = "Invalid model choice or missing API key."
            
            chunk_size = 100  
            total_length = len(summary)
            for start in range(0, total_length, chunk_size):
                chunk = summary[start:start + chunk_size]
                yield json.dumps({
                    "status": "incoming",
                    "stage": "generation",
                    "message": "Generating summary...",
                    "chunk": chunk,
                    "progress": f"{min(start+chunk_size, total_length)}/{total_length}"
                }) + "\n"
                await asyncio.sleep(0.2)  
            
            yield json.dumps({
                "status": "completed",
                "stage": "generation",
                "summary": summary.strip(),
                "message": "Summary generation completed successfully"
            }) + "\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="application/json",
            headers={
                "Content-Type": "application/json",
                "X-Content-Type-Options": "nosniff",
                "Transfer-Encoding": "chunked"
            }
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "status": "error",
                "stage": "processing",
                "summary": "An error occurred while generating the summary.",
                "message": str(e)
            },
            status_code=500
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
