# Document Automation RAG API

![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)

## Purpose

The **Document Automation RAG API** is a document intelligence platform designed to completely automate the processing of unstructured documents: invoices, receipts, and forms. By leveraging Vision-Language Models (VLMs) and Retrieval-Augmented Generation (RAG), the system extracts raw text and highly structured metadata from document images. This allows users to easily index, semantically search, and query their documents through natural language, transforming a pile of messy images into an easily navigable knowledge base.

---

## Architecture & Structure

This project follows SOLID principles, employing a modular, decoupled architecture focused on extensibility and asynchronous performance.

### The "Why" Behind The Technology Stack

- **OpenAI API Standard**: The platform speaks the universal OpenAI API schema. This allows seamless swapping between cutting-edge cloud models (Groq, OpenAI, etc.) and local, privacy-first models (Ollama, vLLM, etc.) without changing a single line of application code.
- **Pydantic**: Used for strict, programmatic schema validation. It ensures the Vision-Language Model strictly adheres to the required data schemas (e.g., extracting specific `VAT` or `buyer` fields), automatically preventing hallucinations and safely parsing LLM outputs into native Python objects.
- **PostgreSQL & pgvector**: True hybrid persistence. Instead of splitting structured metadata into an SQL database and vector embeddings into a separate Vector DB (like Qdrant), everything is consolidated into PostgreSQL. The `pgvector` extension allows storing structured relational data, audit trails, and semantic embeddings in one database.
- **FastAPI & uv**: FastAPI provides a fast, asynchronous, non-blocking HTTP framework, meaning heavy LLM I/O operations don't freeze the server. `uv` is used for fast Python dependency management.

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
| Endpoint | Method | Description |
| - | - | - |
| `/health` | `GET` | Verifies the operational status of the API and its connection to the LLM backend. |
| `/documents/upload` | `POST` | Accepts an image file, assigns a UUID, queues it (`202 Accepted`), and begins background VLM extraction. |
| `/documents` | `GET` | Retrieves a paginated list of all uploaded documents. |
| `/documents/{document_id}` | `GET` | Retrieves the processing status, structured JSON data, and parsed text for a specific document. |
| `/documents/{document_id}` | `PATCH` | Updates the text, structured data, or status of an existing document. |
| `/documents/{document_id}` | `DELETE` | Deletes a document and its embeddings from the database. |
| `/documents/{document_id}/index` | `POST` | Chunks the extracted text (alongside its metadata) and embeds it into the PostgreSQL vector database. |
| `/documents/index:batch` | `POST` | Finds all completed documents that have not been indexed yet, and indexes them in batch. |
| `/rag/search` | `POST` | Performs a semantic vector search across all indexed documents based on a query. |
| `/rag/answer` | `POST` | End-to-end RAG workflow: Routes the query, retrieves context from pgvector, and generates a precise LLM answer based strictly on the retrieved documents. |

---

## Prerequisites & Setup

> **Important!** `docker-compose.yml` handles setting up the database and LLM endpoint automatically.<br>
> The default (in .env file) LLM endpoint is Ollama running on port `11434`.<br>
> The default database is PostgreSQL running on port `5432`.<br>
> Default model for VLM is `llama3-vision`.<br>
> Default model for text embedding is `nomic-embed-text`.<br>
> You can change the database and LLM endpoint in the .env file.

If not using docker-compose, you need to set up the external dependencies yourself. <br>
Before running the application, ensure the external dependencies are accessible:
1. **Database**: A running instance of PostgreSQL with the `pgvector` extension installed.
2. **LLM Endpoint**: Access to an OpenAI-compatible API endpoint (either a local server like Ollama, or a cloud provider like Groq/OpenAI).

### Environment Configuration

Copy the example environment file and configure it.

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

A critical component of this pipeline is the automated evaluation suite. Testing a non-deterministic LLM pipeline requires more than standard unit tests. It requires LLM as a Judge grading and exact match parsing metrics.

### Applied Metrics
1. **Extraction Accuracy (Exact Match)**: The system parses complex JSON structures directly from images. Next, it evaluates the core financial data (e.g., `kwota_koncowa` / `total_gross_worth`) by comparing the pipeline's numerical output against the dataset's ground truth.
2. **Retrieval & Generation Quality (LLM Judge)**: An advanced LLM (e.g., Llama 3.1 70B, gpt-4o-mini, gpt-5, gpt-4o) acts as an impartial judge to grade the pipeline's generated RAG answers. The judge evaluates whether the answer directly and accurately addresses the query using the retrieved context, assigning a binary `1` (Pass) or `0` (Fail).

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

This project is built with containerization strategies. Understanding how the `Dockerfile` is structured is key to extending the infrastructure.

### Core Docker Concepts

#### Dockerfile

A plain-text recipe of instructions that Docker uses to assemble a reproducible, isolated filesystem (an "image") containing the application and all its dependencies. It acts as a blueprint for creating the application's execution environment, ensuring consistency across different systems and preventing "it works on my machine" issues. It can be compared to an instruction set in a recipe. In this project, the Dockerfile is used to build the api, run it locally using docker compose, but it can also be used to deploy the api to a remote server. Every `Dockerfile` uses standard commands to assemble the image:

- `FROM` - specifies the base image to start from. In this case, it is `python:3.11-slim-bullseye`.
- `WORKDIR` - sets the working directory for the subsequent commands. In this case, it is `/app`.
- `COPY` - copies files from the host machine to the container. In this case, it is copying the `requirements.txt` file to the container.
- `RUN` - runs commands in the container. In this case, it is running `uv sync --frozen` to install the dependencies.
- `EXPOSE` - exposes ports from the container to the host machine. In this case, it is exposing port `8000`.
- `CMD` - specifies the command to run when the container starts. In this case, it is running `uv run python -m src.main`.

-- Source: [Docker Documentation](https://docs.docker.com/reference/dockerfile/)

#### .dockerignore

Similar to `.gitignore`, this file dictates which local files/folders should NOT be sent to the Docker daemon. Excluding directories like `.venv/` or large `data/` folders keeps the build process fast and the image lightweight.

Besides the obvious security benefits, another advantage of using `.dockerignore` is the ability to speed up the build process and reduce the size of the image.

Typical items to ignore include:
- Dependency directories (e.g., node_modules/)
- Build artifacts (e.g., dist/, build/)
- Local logs and temporary files
- Version control directories (e.g., .git/, .svn/)
- Editor configuration files (e.g., .idea/, .vscode/)
- Large data files that are not needed for the build (e.g., database dumps, large datasets)
- Sensitive information (e.g., passwords, API keys, private keys)

-- Source: [Docker Documentation](https://docs.docker.com/build/concepts/context/)

#### Docker Context

A Docker context is a configuration containing all the information required to manage resources on a Docker daemon from a single client. Contexts allow switching between different Docker environments (such as local, remote, or cloud based) without modifying Docker CLI configuration.

Key concepts:
- Each context includes name, description, endpoint configuration (e.g., host URL), and TLS certificates.
- The `default` context typically connects to the local Docker daemon via `unix:///var/run/docker.sock` (or `npipe:////./pipe/docker_engine` on Windows).
- The active context determines which Docker daemon the commands target, unless explicitly overridden by the `DOCKER_CONTEXT` environment variable or the `--context` flag.
- Contexts allow to manage multiple environments from a single terminal, such as pushing to staging or managing a remote production server.

Useful commands:
- `docker context ls` : Lists all available contexts.
- `docker context inspect <name>` : View the detailed configuration of a specific context.
- `docker context use <name>` : Switch your active context.

-- Source: [Docker Documentation](https://docs.docker.com/engine/manage-resources/contexts/)

### Image Layers Under the Hood

Docker image layers are the fundamental building blocks of a Docker image. Each layer represents a set of filesystem changes - such as additions, deletions, or modifications - created by a single instruction in a `Dockerfile` (e.g., `FROM`, `RUN`, `COPY`). These layers are stacked sequentially to form the complete image.

#### Key points about image layers:

- Immutability : Once a layer is created, it cannot be changed. Immutability allows for efficient caching and reuse.
- Layer Sharing : Layers can be shared between images. For example, if multiple images use the same base image, those base layers are downloaded and stored only once, saving bandwidth and storage.
- Build Efficiency : When building an image, Docker reuses unchanged layers from previous builds, which speeds up the build process. When you rebuild an image, Docker reuses cached layers until it hits an instruction where the files or commands have changed. Once a layer cache is invalidated, all subsequent layers are rebuilt from scratch.
- Container Filesystem : When a container is started from an image, Docker creates a union filesystem by stacking the image layers and adding a new, writable layer on top for the container. This allows multiple containers to share the same underlying image layers while maintaining their own changes.

#### Example layering process:

1. The first layer might add a base operating system and package manager.
2. The next layer installs a runtime (e.g., Python).
3. Another layer copies in application dependencies.
4. Further layers add the application code.

This structure allows you to extend images by reusing existing layers and only adding what your application needs.

You can inspect the layers of an image using the docker image history command.

-- Source: [Docker Documentation](https://docs.docker.com/get-started/docker-concepts/building-images/understanding-image-layers/)

### Caching Performance & Instruction Order

Caching performance and instruction order are critical factors in optimizing Docker image builds. Here’s how they work together:

#### Caching Performance

- Docker uses a build cache to speed up image builds by reusing previously built layers.
- If an instruction and its dependencies (files, environment, etc.) haven't changed, Docker reuses the cached layer instead of rebuilding it.
- This reduces build time and resource usage, making builds faster and more efficient.
- When a layer is invalidated (due to changes in the instruction or files it depends on), all subsequent layers must also be rebuilt. This is known as cache invalidation.

#### Instruction Order

- The order of instructions in your `Dockerfile` directly affects cache usage.
- Placing frequently changing instructions (like `COPY src/ /app/src/`) later in the `Dockerfile` helps maximize cache reuse for earlier steps (such as installing dependencies).
- For example, copying only package definition files (like `pyproject.toml` and `uv.lock`) before installing dependencies allows Docker to cache the dependency installation step. If only your application code changes, Docker can reuse the cached dependency layer, avoiding unnecessary reinstallations.

#### Best Practices

- Order your `Dockerfile` instructions so that the steps least likely to change come first.
- Keep your build context small to reduce cache invalidation and speed up builds.

**Cache-inefficient Example:**

```dockerfile
COPY . /app/          # Copies ALL code — changes on every git commit
RUN uv sync --frozen  # Cache invalidated every commit — re-downloads all packages!
```

**Optimized Example (Our Approach):**

```dockerfile
COPY pyproject.toml uv.lock ./   # Only changes when dependencies change
RUN uv sync --frozen             # Cache hit on every normal code change
COPY src/ /app/src/              # Changes on every commit, but no slow steps follow
```

In this optimized example, dependencies are installed before copying the rest of the code, so changes to application files don't invalidate the cache for dependency installation. This turns a 3-minute deployment into a ~5-second rebuild during active development.

#### Multi-Stage Builds

`Dockerfile` in this project utilizes Multi-Stage Build pattern:

1. **Stage 1 (Builder)**: Uses a Debian-based image. It installs system dependencies and `uv` package manager to create a Python virtual environment (`.venv`).
2. **Stage 2 (Runtime)**: Starts fresh from a lightweight `python:slim` base image. It copies only the virtual environment from the Builder stage. 

This guarantees that our final production image contains no unnecessary system dependencies, reducing the image size and security attack surface.

-- Source: [Optimize](https://docs.docker.com/build/cache/optimize/)
-- Source: [Image Best Practices](https://docs.docker.com/get-started/workshop/09_image_best/)
-- Source: [Build Cache](https://docs.docker.com/build/cache/)
-- Source: [Using the Build Cache](https://docs.docker.com/get-started/docker-concepts/building-images/using-the-build-cache/)
