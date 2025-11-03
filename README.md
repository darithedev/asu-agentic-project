# Advanced Customer Service AI - Travel Agency

A sophisticated, proof-of-concept customer service application powered by a multi-agent AI system. This application demonstrates a modern, scalable architecture for handling diverse customer inquiries by routing them to specialized AI agents.

## 🎯 Project Overview

This project implements a **multi-agent AI system** that intelligently routes customer queries to specialized agents based on the nature of the inquiry. The system uses different retrieval strategies (RAG, CAG, and Hybrid) tailored to each agent's specific needs, and leverages a multi-provider LLM strategy for cost-effective and high-quality responses.

### Key Features

- **Multi-Agent Architecture**: LangGraph-based orchestrator that routes queries to specialized worker agents
- **Three Specialized Agents**:
  - **Travel Support Agent**: Pure RAG for dynamic travel information
  - **Booking/Payments Agent**: Hybrid RAG/CAG for pricing and payment information
  - **Policy Agent**: Pure CAG for fast, consistent policy responses
- **Multi-LLM Strategy**: AWS Bedrock (Claude Haiku) for cost-effective routing, OpenAI (GPT-4o-mini) for quality responses
- **Real-time Streaming**: Server-Sent Events (SSE) for token-by-token response streaming
- **Persistent Vector Database**: ChromaDB for knowledge base storage

### Architecture

```
User Query
    ↓
FastAPI Backend (/chat endpoint)
    ↓
LangGraph Orchestrator (AWS Bedrock)
    ↓
    ├──→ Travel Support Agent (Pure RAG) ←→ ChromaDB
    ├──→ Booking/Payments Agent (Hybrid RAG/CAG) ←→ ChromaDB + Cached Policies
    └──→ Policy Agent (Pure CAG) ←→ Cached Static Documents
    ↓
Response Streaming (SSE)
    ↓
Next.js Frontend
```

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.13+** (or Python 3.10+)
- **Node.js 20+** and npm
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **AWS Account** with Bedrock access configured ([Setup guide](https://docs.aws.amazon.com/bedrock/latest/userguide/setting-up.html))
  - AWS CLI configured with credentials
  - Bedrock model access enabled for Claude 3 Haiku

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd asu-agentic-project
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
cd backend

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cd backend
touch .env
```

Add the following environment variables to `backend/.env`:

```env
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# AWS Bedrock Configuration (Required)
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Optional: AWS Credentials (if not using default AWS CLI config)
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key

# ChromaDB Configuration (Optional - defaults provided)
CHROMA_DB_PATH=./data/chroma_db
CHROMA_COLLECTION_NAME=travel_agency_kb

# Application Configuration (Optional - defaults provided)
LOG_LEVEL=INFO
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
```

#### Configure AWS Bedrock

Ensure your AWS credentials are configured. You can use one of these methods:

1. **AWS CLI** (Recommended):
   ```bash
   aws configure
   ```

2. **Environment Variables** (add to `.env`):
   ```env
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   ```

3. **IAM Role** (if running on AWS infrastructure)

Make sure your AWS account has access to Bedrock and the Claude 3 Haiku model is enabled in your region.

### 3. Data Ingestion

Before running the application, you need to ingest the mock data into ChromaDB:

```bash
cd backend

# Make sure your virtual environment is activated
source venv/bin/activate  # On macOS/Linux
# or
# venv\Scripts\activate  # On Windows

# Run the ingestion script
python scripts/ingest_data.py
```

**Ingestion Options:**

- **Default behavior**: If the collection already exists, you'll be prompted to clear and re-ingest
- **Force re-ingestion**: `python scripts/ingest_data.py --force`
- **Skip if exists**: `python scripts/ingest_data.py --skip-existing`

The script will:
1. Load documents from `backend/data/mock_data/`
2. Chunk documents based on agent type (different strategies for each agent)
3. Generate embeddings using OpenAI
4. Store in ChromaDB with metadata for filtering

**Expected output:**
```
Starting data ingestion pipeline...
Loading documents from travel_support...
Loading documents from booking_payments...
Loading documents from policy...
Ingestion complete! Collection now contains X documents.
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

#### Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
cd frontend
touch .env.local
```

Add the following:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

This tells the frontend where to find the backend API.

## 🏃 Running the Application

### Start the Backend

```bash
cd backend

# Activate virtual environment if not already active
source venv/bin/activate  # On macOS/Linux
# or
# venv\Scripts\activate  # On Windows

# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Start the Frontend

In a new terminal:

```bash
cd frontend

# Start the Next.js development server
npm run dev
```

The frontend will be available at:
- **Application**: http://localhost:3000

### Using the Application

1. Open http://localhost:3000 in your browser
2. Type a message in the chat interface
3. The orchestrator will route your query to the appropriate agent:
   - **Travel questions** → Travel Support Agent (Pure RAG)
   - **Pricing/Payment questions** → Booking/Payments Agent (Hybrid RAG/CAG)
   - **Policy questions** → Policy Agent (Pure CAG)
4. Watch the response stream in real-time!

### Example Queries

Try these queries to test different agents:

- **Travel Support**: "What are some travel tips for Tokyo?"
- **Booking/Payments**: "How much does a flight to Paris cost?"
- **Policy**: "What is your cancellation policy?"

## 📁 Project Structure

```
asu-agentic-project/
├── backend/
│   ├── app/
│   │   ├── agents/          # Worker agents (orchestrator, travel_support, booking, policy)
│   │   ├── chains/          # LangGraph workflow definition
│   │   ├── config.py       # Configuration management
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── models/         # Pydantic schemas and state models
│   │   └── retrieval/      # RAG, CAG, and Hybrid retrieval implementations
│   ├── data/
│   │   ├── chroma_db/       # ChromaDB persistent storage
│   │   └── mock_data/      # Mock data for ingestion
│   ├── scripts/
│   │   └── ingest_data.py  # Data ingestion pipeline
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Environment variables (create this)
├── frontend/
│   ├── app/                # Next.js app directory
│   ├── components/         # React components
│   │   └── chat/          # Chat interface components
│   ├── lib/                # Utility functions (API client, markdown parser)
│   ├── package.json        # Node.js dependencies
│   └── .env.local         # Frontend environment variables (create this)
└── README.md              # This file
```

## 🔧 Configuration Details

### Backend Configuration

The backend uses Pydantic Settings to load configuration from environment variables. See `backend/app/config.py` for all available settings.

**Required Variables:**
- `OPENAI_API_KEY`: Your OpenAI API key

**Optional Variables:**
- `OPENAI_MODEL`: Defaults to `gpt-4o-mini`
- `OPENAI_EMBEDDING_MODEL`: Defaults to `text-embedding-3-small`
- `AWS_REGION`: Defaults to `us-east-1`
- `BEDROCK_MODEL_ID`: Defaults to `anthropic.claude-3-haiku-20240307-v1:0`
- `API_PORT`: Defaults to `8000`

### Frontend Configuration

The frontend requires:
- `NEXT_PUBLIC_API_URL`: Backend API URL (defaults to `http://localhost:8000`)

## 🧪 Testing the Agents

### Test Travel Support Agent (Pure RAG)

```
Query: "What are some must-see attractions in Paris?"
Expected: Routes to travel_support agent, retrieves from ChromaDB
```

### Test Booking/Payments Agent (Hybrid RAG/CAG)

```
Query: "How much does a hotel package cost?"
Expected: Routes to booking_payments agent, combines dynamic pricing + cached policies
```

### Test Policy Agent (Pure CAG)

```
Query: "What is your cancellation policy?"
Expected: Routes to policy agent, uses cached static documents
```

## 🐛 Troubleshooting

### Backend Issues

**"Failed to initialize Bedrock client"**
- Check AWS credentials are configured correctly
- Verify Bedrock access is enabled in your AWS account
- Ensure the model ID is correct for your region

**"Failed to load collection"**
- Run the data ingestion script first: `python scripts/ingest_data.py`
- Check that ChromaDB directory exists: `backend/data/chroma_db/`

**"OpenAI API key not found"**
- Ensure `.env` file exists in `backend/` directory
- Verify `OPENAI_API_KEY` is set correctly

### Frontend Issues

**"Failed to fetch" or CORS errors**
- Ensure backend is running on `http://localhost:8000`
- Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local`
- Verify CORS is configured in backend (should allow all origins in development)

**"Module not found" errors**
- Run `npm install` in the `frontend/` directory
- Delete `node_modules` and `package-lock.json`, then reinstall

## 📚 API Endpoints

### POST `/chat`
Non-streaming chat endpoint. Returns full response after completion.

**Request:**
```json
{
  "message": "What is your cancellation policy?",
  "session_id": "optional-session-id",
  "conversation_history": []
}
```

**Response:**
```json
{
  "message": "Our cancellation policy allows...",
  "session_id": "session-uuid",
  "agent_type": "policy"
}
```

### POST `/chat/stream`
Streaming chat endpoint using Server-Sent Events (SSE).

**Request:** Same as `/chat`

**Response:** SSE stream with format `data: token\n\n`

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

### GET `/sessions/{session_id}`
Get session information and conversation history.

## 🔍 Development

### Backend Development

```bash
cd backend
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Data Ingestion Development

```bash
cd backend
python scripts/ingest_data.py --force  # Force re-ingest
```

## 📝 License

This project is a proof-of-concept demonstration project.

## 🤝 Contributing

This is a portfolio project. For questions or improvements, please open an issue or submit a pull request.

---

## 📖 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)

