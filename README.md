# AI-Summarization

This project is a FastAPI-based application that extracts text from uploaded PDF files and generates a summary using one of three model options: **Claude**, **Gemini**, or **PodChat**. The backend streams dynamic progress updates in real time, while the frontend (an HTML page) displays only the final summary to users. The detailed progress data is available in the browser’s network/console logs.

## Features

- **PDF Upload:** Upload a PDF file through the web interface.
- **Multiple Model Options:** Choose between:
  - **Claude:** Uses the Claude API.
  - **Gemini:** Uses the Gemini API.
  - **PodChat:** Generates a podcast-style summary via a custom function.
- **Real-time Streaming:** The server sends progress updates in chunks as the summary is generated.
- **Dynamic Updates:** Intermediate status messages (e.g., processing, initialization, generating) are streamed to the client.
- **Frontend Integration:** A simple HTML interface (using Jinja2 templates) that shows the final summary, while progress updates are visible in the browser console or network tab.

## Prerequisites

- Python 3.7 or later
- API keys for Gemini and Claude (set in the `.env` file)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/pdf-summarizer.git
   cd pdf-summarizer
