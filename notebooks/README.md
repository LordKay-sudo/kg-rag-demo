# Notebooks

| Notebook | Roadmap | Description |
|----------|---------|-------------|
| [brca1_structured_vs_literature.ipynb](./brca1_structured_vs_literature.ipynb) | **R8** | BRCA1: BioInsight structured scores beside kg-rag cited quotes — one narrative, shared ENSG id |

## Quick start

Both stacks should be running:

- **kg-rag-demo** API on `http://localhost:8001` (this repo — see [README](../README.md))
- **bioinsight-graph** API on `http://localhost:8000` (sibling repo; optional — the
  notebook degrades gracefully if it is offline)

```bash
cd api
py -3 -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt -r ../notebooks/requirements.txt
jupyter notebook ../notebooks/brca1_structured_vs_literature.ipynb
```

Override base URLs with `KG_RAG_API_URL` and `BIOINSIGHT_API_URL` if your ports differ.
