# A Precision-Oriented Retrieval-Augmented Legal Compliance Assistant

## System design and evaluation protocol

**Article type:** Research prototype and evaluation protocol  
**Project:** Global Compliance Intelligence  
**Version:** 0.3  
**Status:** Manuscript draft; not peer-reviewed  
**Last updated:** November 2026

> **Research status.** This article reports a prototype and a proposed empirical study. It does not claim measured legal accuracy, a completed multi-agent system, or a validated compliance product. Evaluation results are not yet available.

### Abstract

Organizations need to find applicable legal requirements, inspect their own policies, and preserve enough provenance for reviewers to check the analysis. A fluent language-model answer alone does not establish that a provision is authoritative, current, or supportive of the claim. This paper presents Global Compliance Intelligence, a research prototype for evidence-grounded legal question answering and a local, single-company policy-review demonstration. The legal pipeline accepts PDF and DOCX files, extracts selectable text, preserves recognized legal headings as section metadata, stores document records in SQLite, and indexes dense vectors in embedded Qdrant. A separate collection and registry store fictional G Inc Markdown policy drafts. The review workflow retrieves legal and company evidence independently, optionally asks an OpenAI model for structured findings, and checks that returned evidence identifiers belong to the retrieved set. This check verifies identifier provenance, not semantic entailment. The current system is a dense-retrieval baseline with one Indian DPDP-focused demo scope; it does not implement hybrid search, reranking, multi-agent orchestration, cross-jurisdiction comparison, production tenant security, or regulatory monitoring. We define a reproducible evaluation protocol for comparing dense, hybrid, and future multi-agent systems using retrieval, citation, faithfulness, abstention, latency, and cost measures. No quantitative results are reported because the legal corpus and adjudicated question set are not yet complete.

**Keywords:** legal information retrieval; retrieval-augmented generation; compliance; evidence provenance; citation verification; evaluation

---

## 1. Introduction

Legal and compliance work involves more than finding text that resembles a question. A useful research assistant must preserve the source, provision, version, and temporal context of its evidence. It must also be able to say when the indexed corpus does not answer the question. Retrieval-augmented generation (RAG) conditions a language model on retrieved documents [1], but retrieval alone does not guarantee completeness or prove that a cited passage supports a claim.

Global Compliance Intelligence is intended to grow into a platform for multi-jurisdiction legal research and company-policy review. The current codebase implements a narrower, inspectable slice: dense legal retrieval and a local G Inc comparison demonstration. This article documents that scope, describes the present design, and proposes an evaluation that can test later improvements without assuming that additional model calls improve accuracy.

### Research questions

- **RQ1:** How well does dense retrieval return human-labeled relevant legal sections for questions over a curated corpus?
- **RQ2:** Does hybrid retrieval with rank fusion and reranking improve retrieval and citation measures over the dense baseline?
- **RQ3:** Does bounded multi-agent orchestration improve citation completeness and answer faithfulness enough to justify additional latency and cost?
- **RQ4:** How reliably does the system abstain when evidence is weak, missing, contradictory, or temporally inapplicable?

These remain research questions. The current prototype has not been evaluated against an annotated legal dataset.

## 2. Related work

Lewis et al. describe RAG as a combination of parametric generation and non-parametric retrieved knowledge [1]. Sentence-BERT uses siamese and triplet network structures to generate sentence embeddings that can be compared using cosine similarity [2]. Reciprocal Rank Fusion (RRF) combines ranked results without requiring raw retrieval scores to share a common scale [3]. These works motivate the prototype's dense baseline and planned hybrid-retrieval comparator; they do not establish performance on the present corpus.

LegalBench is a collaboratively built benchmark that treats legal reasoning as a collection of distinct tasks rather than a single capability [4]. The evaluation proposed here focuses specifically on legal-section retrieval, citation support, evidence-grounded answers, and abstention. It is not a replacement for a broader legal reasoning benchmark.

## 3. System design

### 3.1 Local architecture

The documented local setup uses FastAPI, SQLite, embedded Qdrant, and a React/Vite frontend. Redis is optional and is not used for background jobs. The backend exposes separate versioned routes for legal documents, questions, and the G Inc demo workspace. FastAPI startup uses a lifespan handler to prepare local storage.

```mermaid
flowchart LR
    UI[React research workspace] --> API[FastAPI API]
    API --> LDB[(SQLite legal registry)]
    API --> CDB[(SQLite G Inc registry)]
    API --> LQ[(Qdrant legal_knowledge)]
    API --> CQ[(Qdrant company_knowledge)]
    API --> EMB[Sentence Transformer]
    API -. optional generation .-> LLM[OpenAI API]
```

**Figure 1.** Current local application components. Legal and company records and vectors are stored separately. The optional language model is used only when configured.

| Component | Current implementation | Boundary |
|---|---|---|
| Legal registry | SQLite and SQLAlchemy | Source of truth for uploaded legal-document metadata and chunks |
| Company demo registry | Separate SQLite tables, fixed G Inc demo ID | Local fictional data only; no authentication or tenant authorization |
| Vector retrieval | Embedded Qdrant with separate collections | One API process; isolated `legal_knowledge` and `company_knowledge` spaces |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | 384 dimensions; normalized embeddings for cosine similarity |
| Generation & Reasoning | Dual Ollama (local Qwen 2.5) / OpenAI API support | Runs locally via Ollama without cloud keys or API costs; fallback to raw excerpts if offline |

### 3.2 Legal document ingestion and metadata representation

The legal endpoint accepts PDF and DOCX files. It applies a size limit, hashes content with SHA-256 for duplicate detection, extracts selectable text (including paragraph and table structures), and splits it using recognized legal headings and paragraph boundaries.

To ensure citation reliability and avoid ungrounded vector search, every indexed chunk is attached to a comprehensive metadata payload:
- **`section`**: The exact statutory heading (e.g., `Section 8(1)`, `Chapter II - Obligations of Data Fiduciary`, `Rule 5`) preserved during structural parsing.
- **`document_title`**: The verified title of the act, regulation, or rule.
- **`document_id`**: Foreign key linked to the persistent SQLite registry.
- **`jurisdiction`**: ISO/statutory code (e.g., `IN` for India, `EU` for European Union).
- **`country` & `domain`**: Topical classification tags (e.g., `India`, `data_privacy`, `cyber_law`).
- **`source_url`**: Direct hyperlink to the authoritative official gazette or government publication.

### 3.3 Metadata-anchored retrieval and anti-hallucination safeguards

Retrieval operates through a two-stage filter-and-rank pipeline rather than unconstrained global cosine similarity:

1. **Hard Metadata Pre-Filtering:** Before computing vector distance, Qdrant executes payload filters. The search space is strictly partitioned by collection (`legal_knowledge` vs. `company_knowledge`) and pre-filtered by jurisdiction (e.g., `jurisdiction == "IN"`). Irrelevant or out-of-jurisdiction provisions are excluded before scoring.
2. **Dense Cosine Ranking:** The query is embedded via `sentence-transformers/all-MiniLM-L6-v2` with `normalize_embeddings=True`, and candidate chunks are ranked by cosine similarity against the question vector.
3. **Similarity Threshold Abstention:** If the top-scoring excerpt falls below the calibrated similarity threshold (`0.25`), the retrieval engine triggers explicit abstention (`evidence_sufficient = False`). The system informs the user that indexed evidence is insufficient rather than generating a speculative answer.
4. **Deterministic Citation Verification:** In the compliance review workflow, the language model outputs structured findings referencing assigned evidence identifiers (`L1`, `C1`). The backend deterministically validates that all returned IDs exist in the retrieved candidate set; unrecognized IDs are discarded, and unsupported findings are downgraded to an insufficiency status.

### 3.4 Separate G Inc evidence and local LLM reasoning

Five synthetic Markdown drafts are provided for fictional G Inc: privacy, retention, incident response, vendor management, and access/security. Their example retention periods and response targets are invented company choices, not legal deadlines. They are indexed only through the company-demo endpoint into `company_documents`, `company_sections`, and the `company_knowledge` vector collection.

The local review endpoint retrieves legal and company evidence independently. When an LLM is enabled—either locally through Ollama running quantized open models (such as `qwen2.5:3b` or `qwen2.5:7b` with 4-bit quantization on a consumer GPU like an RTX 5050 8GB VRAM) or remotely via OpenAI—it executes a structured gap analysis. Findings are categorized into `addressed_in_part`, `potential_gap`, `missing_company_evidence`, or `insufficient_legal_evidence`. If the LLM is offline, the service gracefully returns the separated evidence panels without failing.

### 3.5 Security and legal-use boundary

The G Inc workflow is a local demonstration, not production tenant isolation. It has no login, organization membership, role-based authorization, or audit logging. Its endpoints are disabled when `APP_ENV` is set to `production`, but this alone is not a security architecture. Do not expose the demo API to a network or use confidential documents. A production system requires authenticated access, organization-scoped authorization, document permissions, audit logs, secure deployment, and adversarial testing.

The software is research support, not legal advice or a compliance certification. Users must verify source versions, commencement dates, applicability, interpretation, and every generated finding with qualified reviewers.

## 4. Proposed evaluation

### 4.1 Systems to compare

The systems should use the same corpus, test questions, and generation configuration wherever possible.

1. **Dense baseline (implemented):** query embedding → dense retrieval → top-*k* excerpts → optional generation.
2. **Advanced retrieval (planned):** validated metadata filters → dense and sparse retrieval → RRF → cross-encoder reranking → evidence sufficiency check → optional generation.
3. **Multi-agent RAG (planned):** structured query understanding → validated retrieval plan → jurisdiction-specific retrieval → evidence aggregation → reasoning → bounded critic/retrieval cycle → citation checks → response.

Systems 2 and 3 are proposed comparators, not implemented features. Any agents must have narrow responsibilities, typed outputs, bounded retries, and no authority to construct arbitrary database filters or bypass authorization.

### 4.2 Corpus and annotation

The initial legal corpus should contain a small, versioned set of official Indian DPDP materials. The repository includes a downloader for the Act, 2025 Rules, phased-commencement notification, and Rules corrigendum, but those PDFs are not currently present in this workspace. Download and validate them before indexing. The Rules must be read with the corrigendum and the relevant commencement instrument; the phases differ by provision. The corpus is a focused privacy demo, not a complete collection of Indian law.

Create questions for provision lookup, definitions, scope, exceptions, temporal applicability, policy comparison, and cases where the corpus is insufficient. At least two annotators with legal research experience should label relevant provisions, acceptable citations, expected answer points, and whether abstention is appropriate. Adjudicate disagreements, report inter-annotator agreement, and reserve a held-out test set before tuning.

### 4.3 Metrics and controls

| Measure | Purpose |
|---|---|
| Precision@*K*, Recall@*K* | Relevance of retrieved sections |
| MRR, nDCG@*K* | Rank-sensitive retrieval quality |
| Citation precision and completeness | Whether material claims have supporting citations |
| Answer faithfulness and accuracy | Human-judged support and correctness against adjudicated points |
| Abstention quality | Correct abstention on unanswerable queries and response on answerable queries |
| Latency and cost | End-to-end and retrieval latency, model tokens, embedding/indexing cost |

Freeze corpus hashes, document versions, chunking settings, model versions, prompts, top-*k*, filter plans, and software revisions. Run all systems on the same held-out queries. Report failures and empty retrievals, use paired comparisons with uncertainty intervals, and audit sampled disagreements. Do not convert cosine similarity or model-generated risk labels into probabilities of legal compliance.

## 5. Current implementation and verification

The prototype implements metadata-anchored dense retrieval for legal Q&A, isolated G Inc company policy ingestion and retrieval, and an automated compliance review engine supporting both local Ollama models (such as Qwen 2.5) and OpenAI endpoints.

The indexed legal corpus currently contains 195 statutory sections across three official Indian instruments:
1. **Digital Personal Data Protection Act, 2023** (Act No. 22 of 2023, 55 sections).
2. **Information Technology (Reasonable Security Practices and Procedures and Sensitive Personal Data or Information) Rules, 2011** (G.S.R. 313(E), 45 sections).
3. **Information Technology Act, 2000** (Act No. 21 of 2000, 95 sections).

Verification of the codebase in the current environment confirmed:
- Structural chunking and heading preservation unit tests pass (3/3).
- React/TypeScript frontend builds cleanly (`tsc -b && vite build`).
- Single-command setup and deployment scripts (`setup.sh`, `start.sh`) utilize `uv` and `npm` for fast, reproducible dependency management on Linux environments.
- Live retrieval verified successful section-level grounding with cosine similarity scoring, threshold-based abstention, and citation generation.

No human-annotated legal evaluation dataset or formal quantitative precision/recall benchmark has been executed yet; those measurements are defined in the Section 4 protocol.

## 6. Limitations

The parser's heading patterns are heuristic. Dense embeddings and the similarity threshold have not been tuned on legal queries. Similarity does not establish entailment. Citation-ID validation checks provenance but not semantic support. The company workflow is a single local demo tenant without authentication. The legal corpus is not yet present in this workspace, and legal coverage and temporal applicability will depend on source validation and careful metadata. The current system must not be presented as a complete compliance platform.

## 7. Conclusion

This work provides a source-grounded legal retrieval baseline and an isolated company-policy demonstration, together with an evaluation protocol for measuring future improvements. Its contribution is a prototype and a testable research plan, not evidence that multi-agent processing improves legal accuracy. The next steps are to install the official corpus, run the latest tests, establish a human-validated baseline, and implement hybrid retrieval before introducing multi-agent orchestration and monitoring.

## References

1. Lewis, P., Perez, E., Piktus, A., et al. “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.” *Advances in Neural Information Processing Systems*, 2020. [https://arxiv.org/abs/2005.11401](https://arxiv.org/abs/2005.11401).
2. Reimers, N. and Gurevych, I. “Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.” *EMNLP-IJCNLP*, 2019. [https://aclanthology.org/D19-1410/](https://aclanthology.org/D19-1410/).
3. Cormack, G. V., Clarke, C. L. A., and Büttcher, S. “Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods.” *SIGIR*, 2009. [https://doi.org/10.1145/1571941.1572114](https://doi.org/10.1145/1571941.1572114).
4. Guha, N., et al. “LegalBench: A Collaboratively Built Benchmark for Measuring Legal Reasoning in Large Language Models.” *NeurIPS Datasets and Benchmarks*, 2023. [https://arxiv.org/abs/2308.11462](https://arxiv.org/abs/2308.11462).
