<div align="center">

# A.R.T.H.A
### Advisory for Regulatory and Tax-related Holistic Advisories

**Vectorless RAG for Indian Startup Legal Intelligence**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-149ECA?style=flat-square&logo=react&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?style=flat-square&logo=redis&logoColor=white)
![NVIDIA NIM](https://img.shields.io/badge/NVIDIA_NIM-Kimi_K2.6-76B900?style=flat-square&logo=nvidia&logoColor=white)
![BM25](https://img.shields.io/badge/Retrieval-BM25_Sparse-B8860B?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-8B4513?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active_Development-2E8B57?style=flat-square)

*No vector DB. No embeddings drift. Just exact statutory precision.*

</div>

---

##  Overview

ARTHA is a production-grade legal intelligence platform for Indian startup founders. It replaces conventional vector-similarity RAG with **Vectorless RAG** — BM25 sparse retrieval over full statutory text, paired with long-context reasoning from NVIDIA NIM's Kimi K2.6. The result: precise, citation-backed answers across Indian Corporate Law, GST, FEMA, and SEBI regulations, with no embedding drift and no vector infrastructure to maintain.

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │              FRONTEND                   │
                    │     React + TypeScript · Vite · Tailwind │
                    │  ┌───────────┐  ┌───────────────────┐    │
                    │  │  Chat UI  │  │  Analytics Dash    │    │
                    │  └─────┬─────┘  └─────────┬──────────┘    │
                    └────────┼──────────────────┼───────────────┘
                             │   REST / JSON    │
                    ┌────────▼──────────────────▼───────────────┐
                    │              FASTAPI BACKEND               │
                    │                                            │
                    │   ┌─────────────┐      ┌────────────────┐  │
                    │   │  Query API  │──────▶  Quick Actions │  │
                    │   └──────┬──────┘      │  (memos, clause│  │
                    │          │             │   extraction)  │  │
                    │          ▼             └────────────────┘  │
                    │  ┌───────────────────┐                     │
                    │  │  VECTORLESS RAG   │                     │
                    │  │  BM25 Sparse      │                     │
                    │  │  Retrieval Engine │                     │
                    │  └─────────┬─────────┘                     │
                    │            │  ranked statutory passages    │
                    │            ▼                               │
                    │  ┌───────────────────┐                     │
                    │  │  NVIDIA NIM        │                     │
                    │  │  Kimi K2.6         │                     │
                    │  │  (long-context)    │                     │
                    │  └─────────┬─────────┘                     │
                    │            ▼                               │
                    │   Answer + Statutory Citations              │
                    └───────┬───────────────────┬─────────────────┘
                            │                   │
                     ┌──────▼──────┐    ┌───────▼───────┐
                     │ PostgreSQL  │    │     Redis     │
                     │ (asyncpg,   │    │   (caching)   │
                     │  SQLAlchemy)│    └───────────────┘
                     └─────────────┘
```

##  Features

- **Vectorless RAG** — exact-match keyword retrieval with BM25, tuned for high precision on legal texts.
- **Long-Context LLM** — NVIDIA NIM's Kimi K2.6 reasons over full statutory documents, not chunked fragments.
- **Analytics Dashboard** — track usage, queries, and extracted citations over time.
- **Quick Actions** — generate legal memos, extract key clauses, and surface similar precedents instantly.
- **Interactive Chat** — conversational interface spanning Indian Corporate Law, GST, FEMA, and SEBI regulations.

##  Technology Stack

| Layer | Stack |
|---|---|
| Backend | FastAPI (Python) |
| Database | PostgreSQL (asyncpg + SQLAlchemy) |
| Caching | Redis |
| Retrieval | BM25 (sparse retrieval, no vector DB) |
| Migrations | Alembic |
| Frontend | React + TypeScript, Vite, Tailwind CSS |
| Icons | Lucide React |
| LLM | NVIDIA NIM — Kimi K2.6 |

##  Quick Start (Docker)

The easiest way to run the full stack is Docker Compose.

```bash
git clone <repo-url>
cd artha
cp .env.example .env        # then add your NVIDIA API key + secrets
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | `http://localhost:5173` |
| Backend API Docs | `http://localhost:8000/docs` |

##  Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

##  Security & Secrets

`.gitignore` is pre-configured to exclude:

- `artha.db` and other SQLite files
- `alembic.ini` (may contain DB URLs)
- `.env` files with credentials
- SSL certificates and other secret files

Always use environment variables for sensitive configuration — never commit secrets.

##  License

MIT License.

---

<div align="center">

**A.R.T.H.A** — precision over probability, statute over embedding.

</div>