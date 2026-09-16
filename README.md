# Enterprise IT Support Agentic RAG Copilot

An end-to-end **Agentic RAG-based Enterprise IT Support Copilot** designed to provide grounded, context-aware, and real-time IT support responses.

The system combines **LangGraph, FastAPI, Groq LLM, Pinecone, HuggingFace embeddings, Tavily Web Search, HTML/CSS/JavaScript, SQLite, Docker, and AWS EC2** to create a deployable enterprise IT support solution.

---

## 🚀 Project Overview

Enterprise employees frequently need help with:

- VPN configuration
- Password reset policies
- MFA guidelines
- Software installation
- Laptop troubleshooting
- IT security policies
- Service-desk procedures
- Current vendor or outage information

Traditional keyword search can return irrelevant results, while a standard chatbot may generate unsupported or hallucinated answers.

This project solves the problem using an **Agentic RAG architecture** that decides what action to take based on the user's question and the quality of retrieved evidence.

### Core Principle

```text
User Question
      ↓
Route Question
      ↓
Search Private Company Knowledge Base
      ↓
Evaluate Retrieved Evidence
      ↓
 ┌───────────────┐
 │               │
GOOD           WEAK
 │               │
 ↓               ↓
Generate      Tavily Web Search
from KB            ↓
              Grade Web Evidence
                   ↓
             Generate Answer
```

---

# 1. Business Problem

## Customer

**NovaRetail** is a fictional 3,000-employee retail organization.

## Problem

The internal IT team maintains documents containing:

- VPN instructions
- Password policies
- MFA guidelines
- Software installation procedures
- Laptop troubleshooting guides
- Security policies
- Service-desk runbooks
- IT FAQs

Employees still create repetitive support tickets because:

- They do not know where the correct document is.
- Traditional keyword search may return too many results.
- Generic chatbots may hallucinate answers.
- Internal documents may not contain current external information.
- Some questions require real-time vendor information.

### Example

An employee asks:

> "How do I connect to the company VPN from home?"

The answer should come from the **private company knowledge base**.

Another employee asks:

> "What is the latest Microsoft Teams outage guidance?"

The internal knowledge base may not contain current outage information.

In that situation, the system can use **Tavily Web Search** as an external fallback.

---

# 2. Business Goal

The goal is to build an IT Support Copilot that:

1. Searches trusted private knowledge first.
2. Evaluates retrieved evidence.
3. Uses web search only when required.
4. Rewrites weak queries and retries retrieval.
5. Generates grounded answers.
6. Provides an execution trace for transparency.
7. Allows authorized users to upload new company documents.
8. Can be containerized and deployed to the cloud.

---

# 3. Why Agentic RAG?

A traditional RAG system generally follows:

```text
Question
   ↓
Retrieve
   ↓
Generate
```

This project uses an **agentic workflow**:

```text
Question
   ↓
Route
   ↓
Retrieve Private KB
   ↓
Grade Evidence
   ↓
Choose Next Action
   ↓
 ┌─────────────────────┐
 │                     │
Good Evidence       Weak Evidence
 │                     │
 ↓                     ↓
Generate             Web Search
from KB                 ↓
                     Grade Web
                        ↓
                  ┌─────┴─────┐
                  │           │
                Good        Weak
                  │           │
                  ↓           ↓
              Generate    Rewrite Query
                            ↓
                       Retry Retrieval
                            ↓
                     Retry Limit Reached
                            ↓
                   Insufficient Evidence
```

The agent therefore decides **what to do next based on the current state and evidence quality**.

---

# 4. System Architecture

```text
                         ┌─────────────────────┐
                         │       Employee      │
                         │        / User       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Web Interface    │
                         │   HTML/CSS/JS       │
                         └──────────┬──────────┘
                                    │
                              POST /api/chat
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       FastAPI       │
                         │     Backend API     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      LangGraph      │
                         │  Agentic Workflow   │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    │                                │
                    ▼                                ▼
          ┌─────────────────┐             ┌─────────────────┐
          │  Private KB     │             │  Tavily Search  │
          │    Pinecone     │             │   Web Search    │
          └────────┬────────┘             └────────┬────────┘
                   │                               │
                   └───────────────┬───────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │      Groq LLM       │
                         │ openai/gpt-oss-120b │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Grounded Response   │
                         └─────────────────────┘
```

---

# 5. Agentic RAG Workflow

### Step 1 — Route Question

The system first determines whether the question is:

- Direct conversation
- Enterprise IT support question

```text
Question
   ↓
Router
   ├── Direct → Direct Answer
   │
   └── IT Support → Private KB
```

---

### Step 2 — Retrieve Private Knowledge

The system searches the company's Pinecone knowledge base using semantic similarity.

```text
User Question
      ↓
Embedding
      ↓
Pinecone
      ↓
Relevant Documents
```

---

### Step 3 — Grade Private Evidence

The retrieved documents are evaluated.

```text
Private KB Evidence
        ↓
     Grade
     /   \
  GOOD   WEAK
   |       |
   ↓       ↓
Answer   Web Search
```

---

### Step 4 — Web Search Fallback

If the private knowledge base does not provide sufficient evidence, the agent uses **Tavily** to search the web.

This is useful for questions involving:

- Current outages
- Latest vendor guidance
- Recent software updates
- Current external documentation
- Current IT-related information

---

### Step 5 — Grade Web Evidence

Web search results are evaluated before generating the final response.

```text
Tavily Results
      ↓
Evidence Grade
   /        \
GOOD       WEAK
 |           |
 ↓           ↓
Answer    Rewrite Query
              ↓
           Retry KB
```

---

### Step 6 — Query Rewrite

If retrieval quality is weak, the system rewrites the question into a better search query.

This prevents immediate failure when the user's original question is vague.

---

### Step 7 — Grounded Answer

The final response is generated using the strongest available evidence.

The system can also provide an execution trace showing the decision path.

---

# 6. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Programming Language | Python | Application development |
| Agent Workflow | LangGraph | Stateful agent orchestration |
| LLM | Groq – `openai/gpt-oss-120b` | Routing, grading, rewriting and answer generation |
| LLM Integration | LangChain | LLM and tool integration |
| Embeddings | HuggingFace – `sentence-transformers/all-MiniLM-L6-v2` | Local semantic embeddings |
| Embedding Dimension | 384 | Vector representation |
| Vector Database | Pinecone | Enterprise knowledge retrieval |
| External Search | Tavily | Real-time web search |
| Backend | FastAPI | REST API |
| Frontend | HTML/CSS/JavaScript | Employee-facing interface |
| Audit | SQLite | Decision-path logging |
| Document Processing | PyPDF, python-docx | PDF/DOCX/TXT/MD ingestion |
| Containerization | Docker | Reproducible deployment |
| Cloud | AWS EC2 | Cloud deployment |
| Server | Uvicorn | FastAPI application server |

---

# 7. Project Structure

```text
Enterprise-IT-Support-Agentic-RAG-Copilot/
│
├── app/
│   ├── api/
│   │   └── routes.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   │
│   ├── rag/
│   │   ├── state.py
│   │   ├── vectorstore.py
│   │   └── workflow.py
│   │
│   ├── services/
│   │   ├── audit.py
│   │   └── ingestion.py
│   │
│   └── main.py
│
├── data/
│   └── sample_kb/
│       ├── company_it_handbook.md
│       └── service_desk_runbook.md
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
├── templates/
│   └── index.html
│
├── tests/
│   └── test_ingestion.py
│
├── uploads/
│
├── .env.example
├── .gitignore
├── Dockerfile
├── ingest_sample_kb.py
├── requirements.txt
├── run.py
└── README.md
```

---

# 8. Key Components

## LangGraph

LangGraph controls the stateful Agentic RAG workflow.

It handles:

- Question routing
- Private KB retrieval
- Evidence grading
- Web fallback
- Query rewriting
- Retry logic
- Final answer generation

---

## Pinecone

Pinecone stores the vectorized company knowledge base.

Example:

```text
Company Documents
       ↓
Document Loading
       ↓
Text Chunking
       ↓
HuggingFace Embeddings
       ↓
384-Dimensional Vectors
       ↓
Pinecone
```

---

## HuggingFace Embeddings

The project uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The embedding model runs locally inside the application environment.

This avoids depending on a remote embedding API.

---

## Groq

Groq provides the LLM inference layer.

Current model:

```text
openai/gpt-oss-120b
```

The model is used for:

- Question routing
- Evidence grading
- Query rewriting
- Final answer generation

---

## Tavily

Tavily provides external web search when the private company knowledge base is insufficient.

```text
Private KB
    ↓
Evidence Weak
    ↓
Tavily Search
    ↓
Grade Results
    ↓
Generate Answer
```

---

# 9. Local Development

## Step 1 — Clone Repository

```bash
git clone <your-github-repository-url>
cd Enterprise-IT-Support-Agentic-RAG-Copilot
```

---

## Step 2 — Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 10. Environment Configuration

Create a `.env` file in the project root.

```env
# Groq LLM
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

# Tavily Web Search
TAVILY_API_KEY=your_tavily_api_key

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=fde-it-support-rag
PINECONE_NAMESPACE=company-it-kb

# Local Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Security
ADMIN_API_KEY=your_secure_admin_key

# Application
APP_ENV=development
```

### Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GROQ_API_KEY` | Groq API key | Yes |
| `GROQ_MODEL` | Groq model identifier | Yes |
| `TAVILY_API_KEY` | Tavily web search API key | Yes |
| `PINECONE_API_KEY` | Pinecone API key | Yes |
| `PINECONE_INDEX_NAME` | Pinecone index name | No |
| `PINECONE_NAMESPACE` | Pinecone namespace | No |
| `EMBEDDING_MODEL` | HuggingFace embedding model | No |
| `ADMIN_API_KEY` | Admin authentication key | Yes |
| `APP_ENV` | Application environment | No |

---

# 11. Security

Never commit secrets to GitHub.

Make sure `.env` is included in `.gitignore`.

```gitignore
.env
venv/
__pycache__/
*.pyc
```

Security practices used in the project:

- API keys stored in environment variables
- No hardcoded production secrets
- Admin API protected using `X-Admin-Key`
- Private company knowledge separated using Pinecone namespace
- Upload endpoints restricted to authorized users
- Environment-based configuration

---

# 12. Load Sample Knowledge Base

Run:

```bash
python ingest_sample_kb.py
```

The ingestion pipeline is:

```text
Company Documents
       ↓
Load Documents
       ↓
Chunk Text
       ↓
HuggingFace Embeddings
       ↓
Pinecone Vector Database
```

Supported document formats:

```text
PDF
TXT
MD
DOCX
```

---

# 13. Run Application Locally

```bash
python run.py
```

Or:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 14. Docker Deployment

The application is containerized using Docker.

## Build Docker Image

```bash
docker build -t enterprise-it-support-agent .
```

## Run Docker Container

```bash
docker run -d \
  --name enterprise-it-support-agent \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  enterprise-it-support-agent
```

## Check Container

```bash
docker ps
```

## View Logs

```bash
docker logs --tail 100 enterprise-it-support-agent
```

---

# 15. AWS EC2 Deployment

The application is deployed on an **AWS EC2 instance** using Docker.

### Deployment Architecture

```text
GitHub Repository
       ↓
Docker Build
       ↓
Docker Image
       ↓
AWS EC2 Instance
       ↓
Docker Container
       ↓
FastAPI
       ↓
Port 80 → Port 8000
       ↓
Web Application
```

### AWS Environment

```text
Cloud Provider : AWS
Service        : EC2
OS             : Amazon Linux 2023
Container      : Docker
Backend        : FastAPI
Server         : Uvicorn
Public Port    : 80
App Port       : 8000
```

### Production Docker Run

```bash
docker run -d \
  --name enterprise-it-support-agent \
  --restart unless-stopped \
  -p 80:8000 \
  --env-file .env \
  enterprise-it-support-agent
```

### Verify Container

```bash
docker ps
```

Expected port mapping:

```text
0.0.0.0:80 → 8000/tcp
```

### Health Check

```bash
curl http://localhost/healthz
```

Expected:

```json
{
  "status": "healthy",
  "app": "Enterprise IT Support Agentic RAG Copilot"
}
```

The application runs inside a Docker container on an AWS EC2 instance.

---

# 16. API Endpoints

## Health Check

### `GET /healthz`

Returns application health information.

Example:

```json
{
  "status": "healthy",
  "app": "Enterprise IT Support Agentic RAG Copilot"
}
```

---

## Chat

### `POST /api/chat`

Request:

```json
{
  "question": "How do I reset my company password?"
}
```

The response can contain:

```json
{
  "answer": "Your grounded answer...",
  "source_used": "private_kb",
  "trace": [
    "Router → KB",
    "Private KB retrieval",
    "KB evidence grade → GOOD",
    "Answer generation → PRIVATE KB"
  ],
  "citations": []
}
```

---

## Document Ingestion

### `POST /api/ingest`

Uploads a company document and adds it to the Pinecone knowledge base.

Supported formats:

```text
.pdf
.txt
.md
.docx
```

The endpoint is protected using:

```text
X-Admin-Key
```

---

# 17. Document Upload Workflow

Authorized users can upload new company documents through the application.

```text
Upload Document
      ↓
Validate File Type
      ↓
Load Document
      ↓
Recursive Chunking
      ↓
Generate Embeddings
      ↓
Store in Pinecone
      ↓
Available for Retrieval
```

This allows the company knowledge base to be updated without modifying application code.

---

# 18. Demo Scenarios

## Demo 1 — Private Knowledge Base

### Question

```text
How do I connect to the company VPN from home?
```

### Expected Flow

```text
Router
   ↓
Private KB
   ↓
Retrieve Documents
   ↓
Grade Evidence → GOOD
   ↓
Generate Answer
```

### Key Point

The system uses trusted internal company knowledge instead of unnecessary public web search.

---

# 19. Demo 2 — Company Security Policy

### Question

```text
Can IT support ask me to share my MFA code?
```

### Expected Flow

```text
Router
   ↓
Private KB
   ↓
Evidence Grade → GOOD
   ↓
Private KB Answer
```

### Key Point

The model can answer using company-specific knowledge stored in the enterprise knowledge base.

---

# 20. Demo 3 — Current External Information

### Question

```text
What is the latest Microsoft Teams outage guidance?
```

### Expected Flow

```text
Router
   ↓
Private KB
   ↓
Evidence Grade → WEAK
   ↓
Tavily Web Search
   ↓
Web Evidence Grade
   ↓
Generate Web Answer
```

### Key Point

The agent can use real-time web information when internal knowledge is insufficient.

---

# 21. Demo 4 — Query Rewrite

### Question

```text
My work communication app is acting strange after the new update. What should I do?
```

If the retrieved evidence is weak:

```text
Question
   ↓
Private KB
   ↓
Weak Evidence
   ↓
Web Search
   ↓
Weak Evidence
   ↓
Rewrite Query
   ↓
Retry Retrieval
   ↓
Generate Answer
```

### Key Point

The agent can improve a weak query and retry instead of immediately returning a failure.

---

# 22. Demo 5 — Direct Conversation

### Question

```text
Hello!
```

### Expected Flow

```text
Router
   ↓
Direct
   ↓
Direct Answer
```

This prevents unnecessary vector or web searches for simple conversational messages.

---

# 23. RAG Knowledge Base

Sample company knowledge includes:

```text
company_it_handbook.md
service_desk_runbook.md
```

The knowledge base can be extended with:

- IT policies
- Security guidelines
- VPN documentation
- Password reset procedures
- Software installation guides
- Troubleshooting manuals
- Internal FAQs
- Service desk documentation

---

# 24. Audit and Observability

The application uses SQLite for basic audit logging.

The system can track information such as:

```text
User Question
      ↓
Selected Route
      ↓
Retrieval Result
      ↓
Evidence Grade
      ↓
Tool Used
      ↓
Retry Count
      ↓
Final Answer
```

Example trace:

```text
Router → KB
Private KB retrieval → 4 chunks
KB evidence grade → GOOD
Answer generation → PRIVATE KB
```

This helps with:

- Debugging
- Transparency
- Workflow monitoring
- Understanding agent decisions

---

# 25. Key Project Highlights

- Agentic RAG architecture using LangGraph
- Stateful workflow with conditional routing
- Private enterprise knowledge retrieval
- Pinecone vector database
- Local HuggingFace embeddings
- Groq LLM inference
- Real-time Tavily web search fallback
- Evidence grading
- Query rewriting and retry logic
- Grounded answer generation
- Document upload and ingestion
- PDF/TXT/MD/DOCX support
- FastAPI REST backend
- HTML/CSS/JavaScript frontend
- SQLite audit logging
- Docker containerization
- AWS EC2 cloud deployment
- Environment-based secret management

---

# 26. Project Flow — End to End

```text
                    USER
                      │
                      ▼
              ┌───────────────┐
              │   Web UI      │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │    FastAPI    │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │   LangGraph   │
              │ Agent Workflow│
              └───────┬───────┘
                      │
              ┌───────┴────────┐
              │                │
              ▼                ▼
        Private KB          Direct
         Pinecone           Answer
              │
              ▼
       Grade Evidence
          /       \
       GOOD       WEAK
        │           │
        ▼           ▼
    Generate      Tavily
     from KB      Search
                    │
                    ▼
              Grade Evidence
                /       \
             GOOD       WEAK
               │          │
               ▼          ▼
           Generate    Rewrite
           from Web    Query
                         │
                         ▼
                       Retry
                         │
                         ▼
                Insufficient Evidence
```

---

# 27. Production Deployment Architecture

```text
                    INTERNET
                        │
                        ▼
                ┌───────────────┐
                │    AWS EC2    │
                │ Amazon Linux  │
                └───────┬───────┘
                        │
                        ▼
                ┌───────────────┐
                │     Docker    │
                │   Container   │
                └───────┬───────┘
                        │
                        ▼
                ┌───────────────┐
                │    FastAPI    │
                │   Uvicorn     │
                └───────┬───────┘
                        │
                        ▼
                  LangGraph
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
      Pinecone        Tavily        Groq
      Vector DB      Web Search      LLM
          │
          ▼
   Company Knowledge
```

---

# 28. Security Considerations

The project follows basic security practices:

- Secrets are stored in `.env`
- `.env` should never be committed to GitHub
- Admin document ingestion requires authentication
- API keys are not hardcoded
- Private company data is stored separately in Pinecone
- Environment-specific configuration is supported

For production environments, additional controls can be added:

- HTTPS/TLS
- Reverse proxy
- Authentication and authorization
- Rate limiting
- Secret manager
- Monitoring and alerting
- Cloud logging
- Network restrictions
- IAM policies

---

# 29. Future Improvements

Possible future enhancements include:

- User authentication
- Role-based access control
- HTTPS with a custom domain
- AWS Secrets Manager
- CloudWatch monitoring
- Redis-based session management
- Conversation history
- Feedback and rating system
- Advanced evaluation framework
- RAG evaluation metrics
- Human-in-the-loop escalation
- Ticket creation integration
- ServiceNow/Jira integration
- Multi-tenant knowledge bases
- Automated document synchronization
- CI/CD deployment pipeline
- Infrastructure as Code using Terraform

---

# 30. Example Questions

The application can handle questions such as:

```text
How do I connect to the company VPN?

What is our password reset policy?

Can I share my MFA code with IT support?

How do I install approved software?

What should I do if my laptop is not connecting to Wi-Fi?

What is the latest Microsoft Teams outage guidance?

What are the latest IT security recommendations?

Summarize the company IT handbook.
```

---

# 31. Why This Project Is Different

This is not just a basic chatbot.

The application demonstrates an end-to-end **Agentic RAG system** that can:

```text
Understand
   ↓
Route
   ↓
Retrieve
   ↓
Evaluate
   ↓
Search
   ↓
Rewrite
   ↓
Retry
   ↓
Generate
   ↓
Return Grounded Answer
```

It combines AI engineering with backend development, retrieval systems, tool use, containerization, and cloud deployment.

---

# 32. Skills Demonstrated

### AI / GenAI

- Agentic AI
- Retrieval-Augmented Generation
- Large Language Models
- Prompt Engineering
- Semantic Search
- Embeddings
- Vector Databases
- Tool Calling
- Evidence Grading
- Query Rewriting

### Backend

- Python
- FastAPI
- REST APIs
- Uvicorn
- Pydantic Settings

### AI Frameworks

- LangChain
- LangGraph

### Cloud & DevOps

- Docker
- AWS EC2
- Linux
- Environment Configuration
- Container Deployment

### Data & Storage

- Pinecone
- SQLite
- PDF/DOCX/TXT/Markdown ingestion

---

# 33. Project Outcome

The project provides a practical enterprise IT support solution with:

- Grounded company-specific answers
- Semantic knowledge retrieval
- Real-time web fallback
- Agentic decision making
- Query rewriting
- Document ingestion
- API-based architecture
- Docker-based deployment
- AWS EC2 cloud hosting

The result is a deployable AI-powered IT Support Copilot designed to reduce repetitive IT support questions and help employees find reliable information faster.

---

# 34. Conclusion

**Enterprise IT Support Agentic RAG Copilot** demonstrates how an Agentic RAG workflow can be transformed from an AI prototype into a deployable application.

The system combines:

```text
LangGraph
     +
Groq
     +
Pinecone
     +
HuggingFace Embeddings
     +
Tavily
     +
FastAPI
     +
Docker
     +
AWS EC2
```

to build a practical enterprise AI application capable of retrieving private knowledge, evaluating evidence, using external tools when required, and generating grounded responses.

---

## ⭐ Built With

```text
Python
FastAPI
LangChain
LangGraph
Groq
Pinecone
HuggingFace
Tavily
HTML
CSS
JavaScript
SQLite
Docker
AWS EC2
```

---

## 📌 Project Type

**Enterprise AI / Agentic RAG / Generative AI / FDE Project**

**Deployment:** Docker on AWS EC2

**Architecture:** Agentic RAG with LangGraph

**LLM:** Groq – `openai/gpt-oss-120b`

**Vector Database:** Pinecone

**Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`

**Web Search:** Tavily