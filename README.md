# RAG Invoice Processing API (Production-Grade Reference)

A state-of-the-art document intelligence platform that transforms raw invoice images into searchable, structured insights using a multi-phase AI pipeline.

## 🚀 Key Features

- **Native VLM Mode**: Direct Gemini Vision (Image-to-JSON) for maximum spatial accuracy.
- **Advanced RAG Engine**:
  - **Hybrid Query Routing**: LLM-based router that chooses between SQL, Vector, or Hybrid search.
  - **Semantic Chunking**: Intelligent chunking based on document logic (Header, Line Items, Totals).
  - **Metadata-Aware Indexing**: Pre-filtering support in Qdrant using SQL-aligned payloads.
- **Hybrid Persistence**:
  - **SQLite (SQL)**: Deterministic storage for structured data, line items, and audit trails.
  - **Qdrant (Vector)**: Semantic storage for context-aware Retrieval-Augmented Generation.
- **Enterprise-Ready Infrastructure**:
  - **FastAPI**: Fully asynchronous, non-blocking API with background task orchestration.
  - **Kubernetes**: Complete manifests with HPA (Auto-scaling), PVC (Durable Storage), and Secrets.
  - **Multi-Stage Docker**: Highly optimized image using `uv` and slim runtimes.

---

## 🏗️ Architecture (SOLID & CUPID)

- **Strategy Pattern**: Extensible document processors via `DocumentProcessor` base class.
- **Dependency Inversion**: Clean service layers that depend on abstractions, ensuring testability.
- **Unix Philosophy**: Modular components for LLM, VectorDB, and SQL.

---

## 📂 Project Structure

```text
.
├── src/
│   ├── api/            # Routes, Schemas, Dependencies, Health
│   ├── core/
│   │   ├── llm/        # Gemini SDK, Specialized Prompts
│   │   ├── processors/ # VLMProcessor
│   │   ├── rag/        # Optimized RAG Engine & Hybrid Router
│   │   └── vector_db/  # Qdrant client & metadata-aware indexing
│   ├── models/         # Pydantic (StructuredInvoice) & SQLAlchemy SQL models
│   ├── services/       # Document & RAG service orchestrators
│   └── main.py         # Entry point with Lifespan management
├── k8s/                # Kubernetes manifests (Deployment, HPA, PVC, Service)
├── tests/              # Unit, Integration, and API test suite
├── Dockerfile          # Optimized multi-stage build
├── .dockerignore       # Docker context governance file
└── pyproject.toml      # Modern dependency management (uv)
```

---

## 📡 API Specification

| Method | Endpoint | Status | Description |
|--------|----------|--------|-------------|
| `GET`  | `/health` | `200 OK` | Component-level readiness check |
| `POST` | `/documents/upload` | `202 Accepted` | Upload document and trigger Native Vision-to-JSON mode |
| `GET`  | `/documents/{id}` | `200 OK` / `404` | Full 10-field structured schema + line items |
| `POST` | `/documents/{id}/index` | `200 OK` / `409` | Triggers Metadata-Aware indexing |
| `POST` | `/rag/search` | `200 OK` | Semantic search over indexed chunks |
| `POST` | `/rag/answer` | `200 OK` | Smart routing: SQL/Vector/Hybrid response with sources |

---

## 🛠️ Local Development

```bash
# 1. Install dependencies using uv
uv sync

# 2. Configure environment
cp .env.example .env          # then add your GEMINI_API_KEY

# 3. Run the development server
uv run python -m src.main

# 4. Run the test suite
uv run pytest tests/
```

---

## 🐳 Docker — Concepts & Build Guide

This section explains the Docker concepts required to build and run this project in a container.

### What is a `Dockerfile`?

A `Dockerfile` is a plain-text blueprint that contains a series of instructions telling Docker how to assemble a container image. Each instruction (e.g., `FROM`, `RUN`, `COPY`, `CMD`) adds a new **layer** to the image. When Docker executes a `Dockerfile`, it runs each instruction in sequence, producing a deterministic, reproducible environment that can be shipped and executed identically on any machine that has Docker installed.

Think of it as a recipe: just as a recipe lists the exact ingredients and steps to produce a dish, a `Dockerfile` lists the exact OS dependencies, packages, and application files needed to run your software.

### What is `.dockerignore`?

`.dockerignore` is a context-filtering file (analogous to `.gitignore`) that controls which files and directories are **sent to the Docker daemon** when you run `docker build`. Before Docker begins executing `Dockerfile` instructions, it packages the current directory into a **build context** — a tarball sent over the local socket (or network) to the daemon.

Without `.dockerignore`, this tarball includes everything: `.git/`, `.venv/`, test fixtures, and local databases — potentially hundreds of megabytes of irrelevant data. `.dockerignore` lets you declare what to exclude, so only the minimum necessary files are sent. This has two critical effects:

1. **Smaller context** → faster transfer to the daemon and faster builds.
2. **Correctness** → prevents local artifacts (e.g., a pre-existing `.venv`) from shadowing the files installed inside the image.

This project's `.dockerignore` excludes `.git`, `.venv`, `__pycache__`, `data/uploads/*`, test files, and documentation, while intentionally keeping `pyproject.toml` and `uv.lock` which the builder stage needs.

### What is Docker Context?

The **build context** is the set of files available to Docker during a `docker build` operation. When you run:

```bash
docker build -t my-image .
```

The `.` refers to the build context directory. Docker packages all files in that directory (minus `.dockerignore` exclusions) and sends them to the Docker daemon. Instructions like `COPY` in your `Dockerfile` can only access files that are part of this context — they cannot reach outside it.

This means two things matter for context governance:

- **Path**: The context path determines the root of available files. Using `./` limits scope to the project directory.
- **Exclusions**: `.dockerignore` is your primary tool for shrinking the context to only what's needed.

### How Docker Image Layers Work

Every instruction in a `Dockerfile` that modifies the filesystem (`RUN`, `COPY`, `ADD`) creates a new **immutable layer**. Each layer stores only the **diff** relative to the previous layer — similar to a git commit.

```
Layer 0: FROM python:3.13-slim   →  Base OS filesystem
Layer 1: RUN apt-get install ... →  +libgl1, +libglib2.0-0
Layer 2: COPY pyproject.toml ... →  +dependency files
Layer 3: RUN uv sync --frozen    →  +Python packages in .venv
Layer 4: COPY src/ /app/src/     →  +application source code
Layer 5: CMD [...]               →  Metadata only (no filesystem change)
```

Layers are content-addressed and **cached by Docker**. When you rebuild:
- If a layer's inputs have not changed, Docker reuses the cached layer (near-instant).
- If a layer changes, that layer and **all subsequent layers** are invalidated and rebuilt.

Layers are also shared across images: if two images share the same base (`python:3.13-slim`), Docker stores that layer only once on disk.

### Best Practices for Optimizing Image Build Time

1. **Order instructions from least-to-most-frequently-changed**: Put `apt-get install` before `COPY` so system libraries are cached across code changes.
2. **Use multi-stage builds**: Separate heavy build-time tools (compilers, build-essential) from the lean runtime image. This project's `Dockerfile` uses a `builder` stage with `uv sync` and a minimal runtime stage that only copies the `.venv`.
3. **Minimize layers**: Chain related `RUN` commands with `&&` to avoid creating separate layers for each command.
4. **Clean up in the same layer**: Run `rm -rf /var/lib/apt/lists/*` in the same `RUN` as `apt-get install` — cleaning up in a later layer does not reduce image size because the files still exist in the earlier layer.
5. **Use a `.dockerignore`**: Prevents bloated contexts that slow down build initiation.
6. **Pin exact versions**: `uv sync --frozen` ensures reproducible builds from `uv.lock`, preventing non-deterministic dependency resolution.
7. **Use slim base images**: `python:3.13-slim` instead of `python:3.13` removes ~800MB of unneeded development tools.

### Why Instruction Order in a `Dockerfile` Dictates Caching Performance

Docker's layer cache works on a **first-change-invalidates-all rule**: if any instruction changes, Docker cannot reuse that layer or any layer below it. This means instruction order is a **caching strategy**, not just a stylistic choice.

**Bad ordering (cache-inefficient):**
```dockerfile
COPY . /app/          # Copies ALL code — changes on every git commit
RUN uv sync --frozen  # Cache invalidated every commit — re-downloads all packages!
```

**Optimized ordering (as in this project):**
```dockerfile
COPY pyproject.toml uv.lock ./  # Only changes when deps change (rarely)
RUN uv sync --frozen             # Cache hit on every non-dep code change
COPY src/ /app/src/              # Changes on every commit — but no slow step follows
```

By copying only the dependency manifest files first and running `uv sync` before copying application code, the expensive package installation step is cached for every commit that does not change `pyproject.toml` or `uv.lock`. This turns a 3–5 minute build into a ~10 second rebuild during iterative development.

### Building and Running the Container

**Prerequisites:** Docker installed and running.

**Important Note on AI Models:** This project supports Google Gemini (cloud) and **any OpenAI-compatible endpoint** (including vLLM, LM Studio, Groq, etc.).
If you have a `GEMINI_API_KEY`, the application will use it. If the key is omitted, it automatically falls back to your local endpoint using `OPENAI_BASE_URL`.

**Step 1 — Build the image:**

```bash
docker build -t rag-invoice-api:latest .
```

This reads the `Dockerfile` in the current directory, sends the build context (filtered by `.dockerignore`), and produces a tagged image.

**Step 2 — Run the container:**

```bash
docker run -d \
  --name rag-invoice-api \
  -p 8000:8000 \
  -e GEMINI_API_KEY=your_api_key_here \
  -e OPENAI_BASE_URL=http://host.containers.internal:11434/v1 \
  -v $(pwd)/data:/app/data \
  rag-invoice-api:latest
**Step 1 — Start the environment with Docker Compose:**

```bash
docker-compose up -d --build
```
*(Note: If you use Podman Desktop, use `podman-compose up -d --build`)*

This command will automatically:
1. Start an isolated Ollama container natively inside the virtual machine.
2. Mount your existing `~/.ollama` folder so models don't need re-downloading.
3. Build and start the `rag-invoice-api`.
4. Network them together so the API can reach Ollama internally via `http://ollama:11434/v1` without hitting Windows firewalls.

**Step 2 — Verify models are pulled:**

If you haven't pulled the models yet, you can pull them directly into the running Ollama container:
```bash
docker exec ollama ollama pull llama3.2-vision
docker exec ollama ollama pull nomic-embed-text
```

**Step 3 — Access the API:**

Open your browser and navigate to:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

**Step 4 — View logs:**

```bash
docker-compose logs -f
```

**Step 5 — Stop and remove:**

```bash
docker-compose down
```

---

## ☸️ Kubernetes & Scaling

The project is designed to scale dynamically based on workload:

- **Horizontal Pod Autoscaling (HPA)**: Scales pods from 2 to 10 based on CPU spikes during OCR/VLM tasks.
- **Durable Storage**: Persistent Volume Claims (PVC) ensure your SQLite DB and uploads survive pod restarts.

```bash
# Update k8s/secrets.yaml with your base64-encoded GEMINI_API_KEY (or leave blank to use OPENAI_BASE_URL), then:
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/rag-app.yaml
```
