# YourHeadLaTeX — Backend (BE)

A FastAPI backend that powers a collaborative, real-time LaTeX editor. It stores documents in SQLite, compiles LaTeX source into PDF on demand through the ytotech LaTeX build service, and keeps multiple editors in sync over WebSockets.

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [WebSocket Collaboration](#websocket-collaboration)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## About

**YourHeadLaTeX** is a LaTeX editor project. This repository contains only the **backend service** (`YourHeadLaTeX_BE`) — the REST API, document persistence layer, LaTeX → PDF compiler proxy, and real-time collaboration channel used by the frontend client.

The service exposes:

1. **CRUD endpoints** for LaTeX documents (create, list, read, update, delete).
2. **A compile endpoint** that forwards LaTeX source to a third-party build API and streams back the generated PDF.
3. **A WebSocket endpoint** that broadcasts live edits between users working on the same document.

> Repository: <https://github.com/KevinTheGameMaster/YourHeadLaTex_BE>

---

## Features

- 📄 **Document persistence** — LaTeX documents stored in SQLite via SQLAlchemy 2.0 ORM, with auto-generated short IDs (`uuid4` first 8 chars).
- ⚡ **On-demand PDF compilation** — `POST /compile` proxies the document body to the [ytotech LaTeX build service](https://latex.ytotech.com) and returns the resulting PDF (`application/pdf`).
- 👥 **Real-time collaboration** — `WS /ws/{doc_id}/{user_name}` broadcasts `edit`, `user_joined`, and `user_left` events to every other participant in the same document room.
- 🔁 **Live cursor sharing** — edit messages carry the sender's cursor position alongside the content.
- 🌐 **Permissive CORS** — enabled for all origins/methods/headers so the frontend can be hosted anywhere during development.
- 📚 **Auto-generated API docs** — Swagger UI at `/docs` and ReDoc at `/redoc` (FastAPI defaults).
- 🛠️ **Configurable via environment variables** — base URL, database URL, and compiler API endpoint are read from `.env`.

---

## Tech Stack

| Layer          | Technology                              |
| -------------- | --------------------------------------- |
| Language       | Python 3.9+ (3.11+ recommended)         |
| Web framework  | FastAPI `0.136.1`                       |
| ASGI server    | Uvicorn `0.46.0` (with `watchfiles`)    |
| ORM            | SQLAlchemy `2.0.30` (Declarative 2.0)   |
| Validation     | Pydantic `2.13.3` / pydantic-settings   |
| Database       | SQLite (`latex_editor.db`)              |
| HTTP client    | httpx `0.28.1` (async)                  |
| WebSockets     | `websockets` `16.0`                     |
| Configuration  | python-dotenv `1.2.2`                   |

---

## Project Structure

```
YourHeadLaTex/
├── main.py                 # FastAPI app, CORS, router registration, startup hook
├── base.py                 # Shared SQLAlchemy DeclarativeBase
├── database.py             # Engine, SessionLocal, get_db(), init_db()
├── requirements.txt        # Pinned Python dependencies
├── .env                    # Local environment variables (git-ignored)
├── latex_editor.db         # SQLite database file (git-ignored)
├── models/
│   ├── __init__.py         # Re-exports models
│   └── document.py         # Document ORM model (documents table)
├── schemas/
│   ├── __init__.py         # Re-exports Pydantic schemas
│   └── document.py         # DocumentCreate / DocumentUpdate / DocumentResponse / CompileRequest
└── routes/
    ├── documents.py        # /documents CRUD router
    ├── compiler.py         # /compile router (ytotech proxy)
    ├── ws.py               # /ws/{doc_id}/{user_name} collaboration router
    └── database.py         # Legacy standalone DB helper (superseded by /database.py)
```

---

## Getting Started

### Prerequisites

- Python 3.9 or newer (3.11+ recommended)
- `pip` and (recommended) a virtual environment

### 1. Clone the repository

```bash
git clone https://github.com/KevinTheGameMaster/YourHeadLaTex_BE.git
cd YourHeadLaTex_BE
```

### 2. Create and activate a virtual environment

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
uvicorn main:app --reload
```

The API is now available at <http://localhost:8000>, with interactive documentation at <http://localhost:8000/docs>.

The database schema is created automatically on startup (`init_db()` runs in the FastAPI `startup` event).

---

## Configuration

| Variable             | Default                                | Description                                                          |
| -------------------- | -------------------------------------- | -------------------------------------------------------------------- |
| `BASE_URL`           | `http://localhost:8000`                | Application base URL; also used as FastAPI's `root_path`.            |
| `DATABASE_BASE_URL`  | `sqlite:///./latex_editor.db`          | SQLAlchemy connection string for the document database.              |
| `USERNAME`           | –                                      | Default/display user name used by the client layer.                  |
| `LATEX_API_PRIMARY`  | `https://latex.ytotech.com/builds/sync`| Sync build endpoint of the third-party LaTeX compilation service.    |

> ⚠️ `.env`, `*.db`, and `venv/` are git-ignored. Never commit real credentials.

---

## API Reference

Base path: `/` (root) — all routes below are registered on the FastAPI app.

### Health check

| Method | Endpoint | Description                                  |
| ------ | -------- | -------------------------------------------- |
| `GET`  | `/`      | Returns `{"status": "ok", "docs": "/docs"}`. |

### Documents — `/documents`

| Method   | Endpoint           | Description                                                        |
| -------- | ------------------ | ------------------------------------------------------------------ |
| `POST`   | `/documents`       | Create a document. Body: `{ "title": str, "content"?: str }`. Default content is a minimal `article` template. |
| `GET`    | `/documents`       | List all documents, newest first (`created_at` descending).         |
| `GET`    | `/documents/{id}`  | Fetch a single document by its 8-character ID. `404` if missing.    |
| `PUT`    | `/documents/{id}`  | Update a document's `content`. `404` if missing.                    |
| `DELETE` | `/documents/{id}`  | Delete a document. Returns `{"message": "Document {id} deleted"}`.  |

**Document response shape**

```json
{
  "id": "a1b2c3d4",
  "title": "My Paper",
  "content": "\\documentclass{article}\n...",
  "created_at": "2026-01-01T12:00:00",
  "updated_at": "2026-01-01T12:05:00"
}
```

### Compiler — `/compile`

| Method | Endpoint    | Description                                                                                       |
| ------ | ----------- | ------------------------------------------------------------------------------------------------- |
| `POST` | `/compile`  | Compile LaTeX to PDF. Body: `{ "content": str, "engine"?: "pdflatex" }`. Returns raw `application/pdf` on success, or `503` with the upstream error log on failure. |

**Request**

```json
{
  "content": "\\documentclass{article}\n\\begin{document}\nHello World!\n\\end{document}",
  "engine": "pdflatex"
}
```

**Success**

```
HTTP/1.1 200 OK
Content-Type: application/pdf
<binary PDF>
```

**Failure**

```json
{
  "detail": {
    "error": "Semua compiler API gagal",
    "log": "Primary (https://latex.ytotech.com/builds/sync): Status 400: ..."
  }
}
```

### Example requests

```bash
# Create a document
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello","content":"\\documentclass{article}\\begin{document}Hi\\end{document}"}'

# List documents
curl http://localhost:8000/documents

# Compile to PDF
curl -X POST http://localhost:8000/compile \
  -H "Content-Type: application/json" \
  -d '{"content":"\\documentclass{article}\\begin{document}Hi\\end{document}","engine":"pdflatex"}' \
  --output out.pdf
```

---

## WebSocket Collaboration

```
ws://localhost:8000/ws/{doc_id}/{user_name}
```

Each `doc_id` acts as a room. Connections are held in memory (`connections: Dict[str, List[WebSocket]]`) and removed automatically when a client disconnects or the socket becomes dead.

### Client → Server

```json
{
  "type": "edit",
  "content": "\\documentclass{article}...",
  "cursor": { "line": 3, "column": 12 }
}
```

### Server → Client

```json
{ "type": "user_joined", "user": "Daniel" }
{ "type": "user_left",   "user": "Daniel" }
{ "type": "edit", "content": "...", "user": "Daniel", "cursor": { "line": 3, "column": 12 } }
```

The sender of an edit is excluded from the broadcast; other participants receive the new content, the author's name, and the cursor position.

> **Note:** collaboration state is process-local. Running multiple Uvicorn workers or replicas will not share rooms — a shared pub/sub layer (e.g. Redis) would be required for horizontal scaling.

---

## Roadmap

- [ ] Persist edits from WebSocket sessions back into the database.
- [ ] Document version history / snapshots.
- [ ] Project/file support (multi-file LaTeX with resources).
- [ ] PDF preview caching and compile result storage.
- [ ] Authentication and per-user document ownership.
- [ ] Redis-backed WebSocket fan-out for multi-worker deployments.
- [ ] Fallback compiler providers when the primary build API is unavailable.

---

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`.
3. Commit your changes using the existing convention, e.g. `[feat] add version history`.
4. Push the branch and open a Pull Request against `main`.

Please keep changes scoped, format Python with a consistent style (PEP 8), and make sure the app still starts with `uvicorn main:app --reload` before opening a PR.

---

## License

MIT License

Copyright (c) 2026 Daniel Kevin Jhon Feko Wahyudi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
