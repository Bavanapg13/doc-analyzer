# Data Extraction API

## Description
This project is a Track 2 submission for **AI-Powered Document Analysis & Extraction**. It provides:

- A protected REST API for document analysis
- A browser-based demo UI served from the same FastAPI application
- Multi-format support for PDF, DOCX, and images
- Automatic text extraction with OCR fallback
- AI-assisted summary generation, entity extraction, and sentiment analysis

The system accepts one Base64-encoded document at a time and returns structured JSON with the extracted key information.

## Submission Links
Update these before final submission:

- Live URL: `ADD_DEPLOYED_URL_HERE`
- GitHub Repository: `ADD_GITHUB_REPO_URL_HERE`
- Demo Video: `ADD_YOUTUBE_OR_DRIVE_LINK_HERE`
- Presentation Deck (Optional): `ADD_SLIDES_LINK_HERE`

## Features
- PDF text extraction with page-order preservation
- DOCX paragraph and table extraction
- Image OCR using Tesseract
- OCR fallback for scanned PDFs
- AI-powered summary generation
- Entity extraction for names, dates, organizations, and monetary amounts
- Sentiment classification as `Positive`, `Neutral`, or `Negative`
- API key authentication using `x-api-key`
- Browser UI for live demonstrations and judging
- Docker-based deployment flow for Render, Railway, Fly.io, or similar platforms

## Architecture Overview
The application uses a layered backend:

1. **FastAPI API Layer**
   - Serves the public UI
   - Exposes `/api/document-analyze`
   - Enforces API key authentication

2. **Extraction Layer**
   - `PyMuPDF` for PDF parsing
   - `python-docx` for DOCX parsing
   - `Pillow` + `pytesseract` for image OCR

3. **Analysis Layer**
   - Optional OpenAI-powered structured extraction when `OPENAI_API_KEY` is present
   - Heuristic fallback for summary, entity extraction, and sentiment if no external LLM is configured

4. **Async Layer**
   - Celery wiring included for future background job scaling

## Tech Stack
- Backend: Python, FastAPI
- Async worker: Celery
- OCR: Tesseract, `pytesseract`
- PDF parsing: PyMuPDF
- DOCX parsing: `python-docx`
- Image handling: Pillow
- Sentiment fallback: VADER Sentiment
- Optional AI model integration: OpenAI chat models
- Deployment: Docker, Render-compatible config

## AI Tools Used
Document all AI assistance here as required by the hackathon.

Currently documented for this repository:

- OpenAI Codex / ChatGPT-style coding assistant used for scaffolding, refactoring, UI generation, and README drafting
- OpenAI API integration supported inside the application for document understanding when configured

If you also used GitHub Copilot, Claude, Gemini, Cursor, or any other AI tool during development, add them explicitly before submission.

## Project Structure
```text
your-repo/
|-- README.md
|-- requirements.txt
|-- .env.example
|-- Dockerfile
|-- render.yaml
`-- src/
    |-- main.py
    |-- config.py
    |-- models.py
    |-- security.py
    |-- celery_app.py
    |-- tasks.py
    |-- exceptions.py
    |-- static/
    |   |-- index.html
    |   |-- styles.css
    |   `-- app.js
    `-- services/
        |-- extraction.py
        |-- ocr.py
        |-- analysis.py
        |-- heuristics.py
        `-- pipeline.py
```

## API Contract
### Endpoint
`POST /api/document-analyze`

### Headers
```text
Content-Type: application/json
x-api-key: YOUR_SECRET_API_KEY
```

### Request Body
```json
{
  "fileName": "sample1.pdf",
  "fileType": "pdf",
  "fileBase64": "JVBERi0xLjQKJcfsj6IKNSAwIG9iago8PC9UeXBlIC9QYWdl..."
}
```

### Success Response
```json
{
  "status": "success",
  "fileName": "sample1.pdf",
  "summary": "This document is an invoice issued by ABC Pvt Ltd to Ravi Kumar on 10 March 2026 for an amount of Rs 10,000.",
  "entities": {
    "names": ["Ravi Kumar"],
    "dates": ["10 March 2026"],
    "organizations": ["ABC Pvt Ltd"],
    "amounts": ["Rs 10,000"]
  },
  "sentiment": "Neutral"
}
```

## Setup Instructions
### Local Python setup
1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`.
5. Update `.env` values.
6. Run the server:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```
7. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

### Docker setup
This is the easiest deployment path because the Docker image installs Tesseract automatically.

```bash
docker build -t doc-analyzer .
docker run -p 8000:8000 --env-file .env doc-analyzer
```

## Environment Variables
See `.env.example`.

- `API_KEY`: required API key checked against `x-api-key`
- `ANALYSIS_PROVIDER`: `auto`, `openai`, or `heuristic`
- `OPENAI_API_KEY`: enables OpenAI-powered extraction
- `OPENAI_MODEL`: model used when OpenAI analysis is enabled
- `TESSERACT_CMD`: optional custom path to the Tesseract binary
- `MAX_FILE_SIZE_MB`: request size safety limit
- `MAX_ANALYSIS_CHARACTERS`: trims oversized extracted text before analysis
- `CELERY_BROKER_URL`: Celery broker connection string
- `CELERY_RESULT_BACKEND`: Celery result backend

## Approach
### 1. Extraction strategy
- **PDF**: extract embedded text in reading order with PyMuPDF
- **Scanned PDF**: render page to image and run OCR when embedded text is weak
- **DOCX**: read paragraphs and tables while preserving layout blocks
- **Image**: preprocess and OCR the image with Tesseract

### 2. Summary strategy
- Prefer OpenAI structured analysis when configured
- Fall back to extractive summarization using sentence scoring when no LLM is available

### 3. Entity extraction strategy
- In AI mode, request structured JSON directly from the model
- In fallback mode, use regex and heuristic extraction for:
  - names
  - dates
  - organizations
  - monetary amounts

### 4. Sentiment strategy
- Return only `Positive`, `Neutral`, or `Negative`
- Use conservative fallback thresholds so business documents are not over-labeled

## Demo Flow
The home page at `/` provides a clean frontend for demonstrations:

- Enter the API key
- Upload a PDF, DOCX, or image
- Run the analysis
- Review summary, entities, sentiment, and raw JSON

For judges or technical review, FastAPI docs are also available at `/docs`.

## Deployment Guidance
### Render
1. Push the repository to GitHub.
2. Create a new Render Web Service.
3. Choose **Deploy from a repo** or use `render.yaml`.
4. Set required environment variables:
   - `API_KEY`
   - `ANALYSIS_PROVIDER`
   - `OPENAI_API_KEY` if using OpenAI analysis
5. Deploy and verify `/health`, `/`, and `/api/document-analyze`.

### Recommended production settings
- Use Docker deployment so OCR works without extra manual package installation
- Set `ANALYSIS_PROVIDER=openai` if you want stronger summaries and entities
- Keep the app live for at least 48 hours after submission

## Known Limitations
- OCR quality depends on document clarity and Tesseract availability
- Heuristic fallback is reliable for basic extraction but less accurate than an LLM on complex layouts
- Very large documents are truncated before analysis to keep response times stable
- Currency symbols embedded in certain DOCX fonts can normalize inconsistently depending on source encoding

## Verification Notes
The current implementation has been smoke-tested for:

- Auth failure on missing API key
- Successful DOCX analysis
- Successful PDF analysis
- Clean error handling for OCR when Tesseract is unavailable

## Suggested Demo Video Script
For a 2 to 5 minute submission video:

1. Open the live app homepage
2. Show the upload UI and explain supported formats
3. Run one PDF or DOCX analysis
4. Show the JSON response and extracted entities
5. Open `/docs` briefly to show the official API endpoint
6. Show the GitHub README and deployment notes

## Future Improvements
- Better table-aware extraction for complex invoices
- Layout-aware chunking for long reports
- Confidence scores for extracted entities
- Batch processing dashboard on top of the existing Celery wiring
