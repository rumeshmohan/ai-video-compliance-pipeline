# Brand Guardian AI 

AI-powered video compliance auditing system/ai-video-compliance-pipeline. Analyzes YouTube videos against brand guidelines using Azure Video Indexer, Azure AI Search (RAG), and LangGraph.

## Architecture

```
YouTube URL → Azure Video Indexer → Transcript + OCR → RAG Audit (LLM) → Compliance Report
```

**Workflow:** `START → Indexer Node → Auditor Node → END`

## Setup

### 1. Install dependencies
```bash
uv sync
```

### 2. Configure environment variables
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

### 3. Index your compliance documents
```bash
uv run python backend/scripts/index_documents.py
```

### 4. Run the API server
```bash
uv run uvicorn backend.src.api.server:app --reload
```

### 5. Run CLI simulation
```bash
uv run python main.py
```

## Environment Variables

| Variable | Description |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Chat model deployment name |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding model deployment name |
| `AZURE_OPENAI_API_VERSION` | API version (e.g. `2024-02-01`) |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search endpoint |
| `AZURE_SEARCH_API_KEY` | Azure AI Search API key |
| `AZURE_SEARCH_INDEX_NAME` | Name of your search index |
| `AZURE_VI_ACCOUNT_ID` | Azure Video Indexer account ID |
| `AZURE_VI_LOCATION` | Azure Video Indexer location |
| `AZURE_VI_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_RESOURCE_GROUP` | Azure resource group name |
| `AZURE_VI_NAME` | Azure Video Indexer resource name |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Azure Monitor connection string (optional) |

## API Endpoints

- `POST /audit` — Submit a video URL for compliance auditing
- `GET /health` — Health check

### Example Request
```bash
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtu.be/abc123"}'
```
