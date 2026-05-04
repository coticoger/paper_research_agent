# AI Paper Search Workflow

This directory contains a LangGraph-based paper search workflow that routes a user request into a multi-step research pipeline.

## Overview

The current flow is:

1. `commit_agent`
2. `human_review`
3. `router`
4. `paper_search_agent`
5. `search_agent`
6. `relevance_agent`
7. `summary_agent`
8. `validation_agent`

The pipeline is designed to:

- refine the user request into a structured research instruction
- search papers from arXiv and PubMed
- score relevance
- summarize the most relevant papers using PDF tools when possible
- validate whether the final papers really match the user intent

## Directory Structure

```text
ai/
├── .env
├── README.md
├── requirements.txt
├── paper_search_graph.png
└── src/
    ├── agent/
    ├── graph/
    ├── prompts/
    ├── schemas/
    ├── tools/
    ├── config.py
    ├── run.py
    └── utils.py
```

## Requirements

Install dependencies:

```bash
cd ai
pip install -r requirements.txt
```

## Environment Variables

Create or update `ai/.env` with the following values:

```env
OPENAI_API_KEY=your_openai_api_key
PUB_MED_KEY=your_pubmed_api_key_optional
EXA_API_KEY=your_exa_api_key_optional
```

Notes:

- `OPENAI_API_KEY` is required.
- `PUB_MED_KEY` is optional, but useful for PubMed rate limits.
- `EXA_API_KEY` is optional for the current main paper search flow.

## How To Run

Run from the `ai` directory:

```bash
cd ai
python src/run.py "Find papers about retrieval-augmented generation for enterprise QA"
```

## Output

During execution, the workflow may generate:

- graph output:
  - `ai/paper_search_graph.png`
  - or `ai/paper_search_graph.mmd`
- intermediate memory files under:
  - `ai/src/memory/<timestamp>/`

Typical saved files include:

- `paper_search.json`
- `scored_papers.json`
- `paper_summaries.json`
- `validated_papers.json`

## Main Components

### Agents

- `src/agent/commit_agent.py`
  - converts the raw user query into a structured task
- `src/agent/human_review.py`
  - allows manual topic review before routing
- `src/agent/router.py`
  - routes the task to the correct subgraph
- `src/agent/paper_search/search_agent.py`
  - collects candidate papers from search tools
- `src/agent/paper_search/relevance_judge.py`
  - scores paper relevance
- `src/agent/paper_search/summary_agent.py`
  - downloads PDFs when possible and summarizes papers
- `src/agent/paper_search/valid_agent.py`
  - validates final paper suitability and can trigger retry

### Tools

- `src/tools/research_tools.py`
  - arXiv and PubMed search tools
- `src/tools/pdf_tools.py`
  - PDF download and section extraction tools
- `src/tools/file_tools.py`
  - workspace file read and write tools

## Current Notes

- The workflow currently relies on live model calls and network access.
- The validation agent can trigger another search round when no good papers are found.
- Some modules outside the main paper search path are still experimental.

## Troubleshooting

### `OPENAI_API_KEY` error

If you see an API key error, make sure `ai/.env` exists and contains:

```env
OPENAI_API_KEY=...
```

### Graph image is not saved as PNG

If PNG rendering fails, the code falls back to saving Mermaid text as:

```text
ai/paper_search_graph.mmd
```

### Search loops unexpectedly

Check:

- `src/agent/paper_search/valid_agent.py`
- `src/graph/paper_search_graph.py`
- retry settings in `src/config.py`

## Quick Start

```bash
cd ai
pip install -r requirements.txt
python src/run.py "Find recent papers about multimodal RAG"
```
