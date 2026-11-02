# Global Compliance Intelligence

**Research paper:** Open the standalone, responsive [web article](RESEARCH_PAPER.html) or read its Markdown source in [RESEARCH_PAPER.md](RESEARCH_PAPER.md). The manuscript is a prototype report and evaluation protocol, not peer-reviewed research and not a claim of measured system accuracy.

Research-oriented baseline for source-grounded legal Q&A. This repository implements the **first milestone** from `prompt.txt`: a React/Vite UI, FastAPI service, local SQLite document registry, embedded Qdrant dense retrieval, optional Redis health check, PDF/DOCX extraction, legal-heading-aware chunking, embeddings, and citation-bearing Q&A.

The project folder contained two PowerPoint review templates, an idea note, and a LangChain demo. None is a validated legal source, so they were not imported. Upload only legal documents that have been classified and checked by a project owner. Metadata not supplied by the uploader stays unknown.

## Requirements (no Docker)

- Python 3.11 or newer
- Node.js 20 or newer and npm
- Internet access on first run to download packages and the embedding model
- Optional OpenAI API key for generated answers. Without it, the API returns retrieved excerpts and citations without generating a legal conclusion.

## Quick Start (Linux / macOS)

Setup everything with one command:
```bash
./setup.sh
```

Launch both the Backend and Frontend with one command:
```bash
./start.sh
```
- Web UI: <http://localhost:5173>
- API Docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

Upload demo company policies and legal docs (optional):
```bash
./backend/.venv/bin/python3 scripts/upload_demo_data.py
```

## Quick Start (Windows PowerShell - No WSL)

Setup everything with one command in PowerShell:
```powershell
.\setup.ps1
```

Launch both the Backend and Frontend with one command:
```powershell
.\start.ps1
```
- Web UI: <http://localhost:5173>
- API Docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

Upload demo company policies and legal docs (optional):
```powershell
.\backend\.venv\Scripts\python.exe scripts\upload_demo_data.py
```

## Local data services

From the repository root, create your environment file:

```powershell
Copy-Item .env.example .env
```

The defaults need no database, vector database, or cache service to be installed separately. SQLite stores the registry in `data/compliance.db`; Qdrant runs embedded in the API process and persists vectors in `data/qdrant`. Redis is optional and unused in this milestone. Do not commit real credentials. The default embedding model outputs 384 dimensions and downloads on first use.

## Install the focused India privacy demo corpus

This demo corpus covers the Digital Personal Data Protection Act and its 2025 Rules, not every Indian law. It includes the Act, final Rules, phased-commencement notification, and Rules corrigendum. They are linked from official [India Code](https://www.indiacode.nic.in/bitstream/123456789/22037/2/a2023-22.pdf), [eGazette](https://egazette.gov.in/WriteReadData/2025/267650.pdf), and [MeitY](https://www.meity.gov.in/static/uploads/2025/12/3c7ebbae0e5456f493f486e6845df86b.pdf) sources. The Rules must be read with their corrigendum and commencement notification; applicability is phased.

After installing Python packages, run these commands from the repository root. The download script checks each file's PDF header and writes a SHA-256 manifest. Start the API first; then run the upload script in another PowerShell window to register and embed the files.

```powershell
.\scripts\download_indian_demo_docs.ps1
# Start the API in a separate terminal, then:
.\scripts\upload_indian_demo_docs.ps1
```

Official PDFs and their source URLs are saved under `data/legal/india/dpdp/`. Do not upload draft consultation material or third-party summaries as law.

## G Inc sample company policies

Five synthetic, unapproved policy and procedure drafts are under `data/company/g-inc/`. Retention periods and internal response targets in those examples are fictional choices, not legal deadlines. In the running app, open **Company Review** and upload the Markdown drafts there. They are stored in a separate Qdrant collection and SQLite tables from legal sources. The review endpoint uses the fixed server-side G Inc demo ID; this is not production authentication or multi-tenant security. It is disabled when `APP_ENV=production`, and must only be used locally with fictional data. Set `OPENAI_API_KEY` in `.env` to generate a draft comparison; without a key, the app returns separate retrieved evidence without making a compliance assessment.

To bulk upload the sample policies after starting the API, run:

```powershell
.\scripts\upload_ginc_demo_policies.ps1
```

Then open **Company Review**, ask a policy-versus-law question, and review the legal and company evidence side by side. A generated review still requires `OPENAI_API_KEY`; the review output validates citation IDs against retrieved records but does not prove that each claim is semantically supported. Treat all generated findings as unverified draft research and have a qualified reviewer check them.

## Start the API

```powershell
cd E:\Capstone_projects\backend
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Using the virtual environment's executable directly avoids PowerShell activation policy issues. Keep this terminal open while the API runs. API docs are at <http://localhost:8000/docs>; health status is at <http://localhost:8000/health>. Embedded Qdrant is intended for one API process; don't start multiple workers against the same local Qdrant path.

## Start the UI

In another terminal from the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. The UI supports the document registry, PDF/DOCX upload, source-grounded Q&A, and citation excerpts. Documents are uploaded with optional metadata through the API; missing authority, jurisdiction, effective dates, version, and source URL are not invented.

## API examples

Upload a validated source:

```powershell
curl.exe -X POST http://localhost:8000/api/v1/documents/upload `
  -F "file=@C:\legal\source.pdf" `
  -F "title=Source title as verified" `
  -F "jurisdiction=IN" `
  -F "country=India" `
  -F "domain=data_privacy" `
  -F "authority=Publishing authority" `
  -F "document_type=act" `
  -F "publication_date=2023-08-11" `
  -F "effective_from=2023-08-11" `
  -F "source_url=https://official.example/source"
```

Ask a question:

```powershell
curl.exe -X POST http://localhost:8000/api/v1/query `
  -H "Content-Type: application/json" `
  -d '{"question":"What does the indexed source say about its scope?","jurisdiction":"IN","top_k":5}'
```

The response includes `answer`, exact indexed excerpts with document and section IDs, similarity scores, source URLs where supplied, and an evidence sufficiency flag. The baseline currently uses dense retrieval; hybrid retrieval, reranking, temporal applicability, multi-agent reasoning, auth/tenant isolation, monitoring, OCR, and company-document ingestion are later milestones and are not represented as implemented.

## Database migrations

The initial schema is in `backend/migrations/versions/0001_initial_registry.py`.

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

## Checks

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
cd ..\frontend
npm run build
```

The backend test suite covers legal and company Markdown chunking. No legal evaluation dataset or performance metrics are included; those must be built from human-validated questions and sources.
#

# CAP
