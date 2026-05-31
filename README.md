# Document Automation RAG API

![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)

## Purpose

The **Document Automation RAG API** is a document intelligence platform designed to completely automate the processing of unstructured documents (such as invoices, receipts, and forms). By leveraging Vision-Language Models (VLMs) and Retrieval-Augmented Generation (RAG), the system extracts raw text and highly structured metadata from document images. This allows users to easily index, semantically search, and query their documents through natural language, transforming a pile of messy images into an easily navigable knowledge base.

---

## Architecture & Structure

This project follows SOLID principles, employing a modular, decoupled architecture focused on extensibility and asynchronous performance.

### The "Why" Behind Our Technology Stack

- **OpenAI API Standard**: Rather than locking into a single LLM vendor, the platform speaks the universal OpenAI API schema. This allows seamless swapping between cutting-edge cloud models (like Groq or OpenAI) and local, privacy-first models (like Ollama or vLLM) without changing a single line of application code.
- **Pydantic**: Used for strict, programmatic schema validation. It ensures the Vision-Language Model strictly adheres to our required data schemas (e.g., extracting specific `VAT` or `buyer` fields), automatically preventing hallucinations and safely parsing LLM outputs into native Python objects.
- **PostgreSQL & pgvector**: True hybrid persistence. Rather than splitting structured metadata into an SQL database and vector embeddings into a separate Vector DB (like Qdrant), I consolidated everything into PostgreSQL. The `pgvector` extension allows storing structured relational data, audit trails, and semantic embeddings in a single, ACID-compliant, deterministic database.
- **FastAPI & uv**: FastAPI provides a lightning-fast, fully asynchronous, non-blocking HTTP framework, meaning heavy LLM I/O operations don't freeze the server. `uv` is utilized for modern, incredibly fast Python dependency management and deterministic environment resolution.

### Application Structure

```text
src/
├── api/          # HTTP layer (FastAPI endpoints, routers, dependencies)
├── core/         # Core business logic (DB engine, LLM clients, configuration, processors)
├── models/       # Data layer (Pydantic schemas and SQLAlchemy models)
└── services/     # Orchestration layer (RAG logic and document pipeline coordination)
tests/
├── api/          # Endpoint tests
├── evaluation/   # Automated evaluation suite (VLM Extraction and LLM Judge RAG metrics)
├── integration/  # System integration tests
└── unit/         # Unit tests for core logic
```

### API Endpoints & HTTP Status Codes

The API strictly adheres to REST principles and utilizes specific HTTP status codes to communicate application states:
- `200 OK`: Successful retrieval or completion of synchronous operations.
- `202 Accepted`: Document accepted for asynchronous background processing.
- `400 Bad Request`: Invalid file formats (only `.jpg`, `.jpeg`, `.png` allowed).
- `404 Not Found`: Document ID does not exist in the database.
- `409 Conflict`: Duplicate document upload, or attempting to index a document that hasn't finished processing.
- `422 Unprocessable Entity`: Validation failures (e.g., trying to index a document that failed VLM extraction).
- `500 Internal Server Error`: Unexpected downstream errors (e.g., VLM or VectorDB timeouts).

#### Endpoints
- `GET /health` - Verifies the operational status of the API and its connection to the LLM backend.
- `POST /documents/upload` - Accepts an image file, assigns a UUID, queues it (`202 Accepted`), and begins background VLM extraction.
- `GET /documents` - Retrieves a paginated list of all uploaded documents.
- `GET /documents/{document_id}` - Retrieves the processing status, structured JSON data, and parsed text for a specific document.
- `PATCH /documents/{document_id}` - Updates the text, structured data, or status of an existing document.
- `DELETE /documents/{document_id}` - Deletes a document and its embeddings from the database.
- `POST /documents/{document_id}/index` - Chunks the extracted text (alongside its metadata) and embeds it into the PostgreSQL vector database.
- `POST /documents/index:batch` - Finds all completed documents that have not been indexed yet, and indexes them in batch.
- `POST /rag/search` - Performs a semantic vector search across all indexed documents based on a query.
- `POST /rag/answer` - End-to-end RAG workflow: Routes the query, retrieves context from pgvector, and generates a precise LLM answer based strictly on the retrieved documents.

---

## Prerequisites & Setup

> **Important!** `docker-compose.yml` handles setting up the database and LLM endpoint automatically.
> The default (in .env file) LLM endpoint is Ollama running on port `11434`.
> The default database is PostgreSQL running on port `5432`.
> Default model for VLM is `llama3-vision`.
> Default model for text embedding is `nomic-embed-text`.
> You can change the database and LLM endpoint in the .env file.
> **Note**: In `docker-compose.yml`, if the LLM endpoint is set to `http://ollama:11434`, the hostname `ollama` is resolvable because it is the name of the service defined in the `docker-compose.yml` file itself. This allows the application container to communicate with the Ollama container using the internal Docker network.

Before running the application, ensure the external dependencies are accessible:
1. **Database**: A running instance of PostgreSQL with the `pgvector` extension installed.
2. **LLM Endpoint**: Access to an OpenAI-compatible API endpoint (either a local server like Ollama, or a cloud provider like Groq/OpenAI).

### Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Your `.env` file should look similar to this:
```env
# Fastapi/App Config
PROJECT_NAME="Document Automation RAG API"

# Database Config
POSTGRES_URL="postgresql+asyncpg://user:password@localhost:5432/rag_db"

# LLM Generation Config (VLM / QA)
OPENAI_BASE_URL="http://localhost:11434/v1"
OPENAI_API_KEY="sk-dummy"
GEN_MODEL="llama3-vision"

# LLM Embedding Config
OPENAI_EMBEDDING_BASE_URL="http://localhost:11434/v1"
OPENAI_EMBEDDING_API_KEY="sk-dummy"
EMBED_MODEL="nomic-embed-text"

# Evaluation Judge LLM Config (Optional - used by evaluate_retrieval.py)
JUDGE_LLM_BASE_URL="https://api.groq.com/openai/v1"
JUDGE_LLM_API_KEY="gsk_dummy_key"
JUDGE_LLM_MODEL="llama-3.1-70b-versatile"
```

---

## Execution Guide

You can run the application using three different methods, depending on your environment.

### Option 1: Local Development (Using `uv`)
Best for active development. Runs directly on your host machine without containers.

```bash
# 1. Install dependencies
uv sync

# 2. Run the asynchronous development server
uv run python -m src.main
```

### Option 2: Full Infrastructure (Using `docker-compose`) - **Recommended**
Best for a "one-click" deployment. This spins up the API, the PostgreSQL database, and a local Ollama LLM instance automatically.

> **Note**: It's recommended to use local LLM for embeddings to avoid API costs and rate limits and cloud or larger local VLM for vision-language model tasks.

```bash
# Start all services in detached mode
docker-compose up --build -d

# View API logs
docker-compose logs -f rag-invoice-api
```

### Option 3: Manual Container Deployment (Using `Dockerfile`)
Best if you already have external databases/LLMs and just want to host the API in an isolated container.

```bash
# 1. Build the image
docker build -t doc-auto-api:latest .

# 2. Run the container, linking to your external services
docker run -d \
  --name doc-auto-api \
  -p 8000:8000 \
  --env-file .env \
  doc-auto-api:latest
```

---

## Evaluation & Testing

A critical component of this production-grade pipeline is the automated evaluation suite. Testing a non-deterministic LLM pipeline requires more than standard unit tests; it requires LLM-as-a-Judge grading and exact match parsing metrics.

### Applied Metrics
1. **Extraction Accuracy (Exact Match)**: The system parses complex JSON structures directly from images. We evaluate the core financial data (e.g., `kwota_koncowa` / `total_gross_worth`) by comparing our pipeline's numerical output against the dataset's ground truth.
2. **Retrieval & Generation Quality (LLM Judge)**: We use an advanced LLM (e.g., LLaMA-4-Scout) acting as an impartial judge to grade the system's generated RAG answers. The judge evaluates whether the answer directly and accurately addresses the query using the retrieved context, assigning a binary `1` (Pass) or `0` (Fail).

### Running the Evaluation Suite
The project includes two primary evaluation scripts located in `tests/evaluation/`. They utilize a shared utility module (`eval_utils.py`) to automatically download a randomized subset of the `katanaml-org/invoices-donut-data-v1` dataset to perform live end-to-end testing.

#### 1. VLM Extraction Evaluation
This script tests the Vision-Language Model's ability to extract structured Pydantic data from raw invoice images.

```bash
uv run .\tests\evaluation\evaluate_extraction.py
```

*Real Result Example (100% Exact Match):*
```json
{
  "nazwa_sklepu": "Lawrence LLC",
  "data": "07/29/2018",
  "kwota_koncowa": 482.25,
  "VAT": 43.84
}
```
```text
==========================================
EVALUATION SUMMARY
==========================================
Total Samples Processed : 5
Successful Extractions  : 5
Average Duration/Sample : 2.86s
Exact Match (Amount)    : 5 / 5 (100.0%)
==========================================
```

#### 2. RAG Retrieval Evaluation
This script tests the Vector Database (pgvector) and the LLM routing/generation logic. It safely injects ground-truth documents into the database, runs a suite of challenging Polish queries, evaluates the results, and cleans up the database afterward.

```bash
uv run .\tests\evaluation\evaluate_retrieval.py
```

*Real Result Example (LLM Judge Evaluation):*
```text
--- Query: Czy na dokumencie występuje podatek? ---
Route taken: vector
System Answer: Tak, na dokumencie występuje podatek (VAT). Widoczne jest to w szczegółach produktów, gdzie dla każdego towaru określono stawkę VAT na poziomie 10%.

LLM Judge Evaluation:
GRADE: 1
The System Answer provides a direct and meaningful response to the Query by confirming the presence of tax (VAT) on the document and providing additional details about the tax rates.
```

---

## DevOps & Infrastructure Guide

This project is built with production-grade containerization strategies. Understanding how the `Dockerfile` is structured is key to extending the infrastructure.

### Core Docker Concepts
- **Dockerfile**: A plain-text recipe of instructions that Docker uses to assemble a reproducible, isolated filesystem (an "image") containing the application and all its dependencies.
- **.dockerignore**: Similar to `.gitignore`, this file dictates which local files/folders should NOT be sent to the Docker daemon. Excluding directories like `.venv/` or large `data/` folders keeps the build process fast and the image lightweight.
- **Docker Context**: The set of files located in the specified path (usually `.`) when you invoke `docker build`. The Docker daemon packs this entire context into an archive before building. Minimizing the context (using `.dockerignore`) is crucial for speed.

### Image Layers Under the Hood
Every command (`FROM`, `RUN`, `COPY`) in a `Dockerfile` creates a new, read-only "layer" that sits on top of the previous one. Docker caches these layers. When you rebuild an image, Docker reuses cached layers until it hits an instruction where the files or commands have changed. Once a layer cache is invalidated, all subsequent layers are rebuilt from scratch.

### Caching Performance & Instruction Order
Because of the "first-change-invalidates-all" rule, the order of instructions in our `Dockerfile` dictates our caching performance. 

**Bad ordering (Cache-inefficient):**
```dockerfile
COPY . /app/          # Copies ALL code — changes on every git commit
RUN uv sync --frozen  # Cache invalidated every commit — re-downloads all packages!
```

**Optimized ordering (Our approach):**
```dockerfile
COPY pyproject.toml uv.lock ./   # Only changes when dependencies change
RUN uv sync --frozen             # Cache hit on every normal code change
COPY src/ /app/src/              # Changes on every commit, but no slow steps follow
```
By placing slowly changing files (`pyproject.toml`) and heavy installations (`uv sync`) at the top, and rapidly changing files (source code) at the bottom, we turn a 3-minute deployment into a ~5-second rebuild during active development.

### Optimizing Image Build Time (Multi-Stage Builds)
Our `Dockerfile` utilizes a **Multi-Stage Build** pattern:
1. **Stage 1 (Builder)**: Uses a heavier image. It installs system compilers (like `build-essential`) and the `uv` package manager to compile the Python virtual environment (`.venv`).
2. **Stage 2 (Runtime)**: Starts fresh from a pristine, lightweight `python-slim` base image. It copies only the compiled `.venv` from the Builder stage. 

This guarantees that our final production image contains no unnecessary compilers or cache files, drastically reducing the image size and shrinking the security attack surface.
