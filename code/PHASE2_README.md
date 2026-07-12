# Eunoform Companion — Phase 2 Code Overlay

Copy the contents of this package into the repository root. It is structured so the `code/` directory merges with the existing Phase 1 implementation.

## Install and test without `uv`

```bash
cd code
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
```

## Run the local API

```bash
uvicorn app.main:app \
  --app-dir apps/companion-service \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
```

Then open `http://127.0.0.1:8000/docs`.

## Repository README

Apply `README_PHASE2_UPDATE.diff` from the repository root:

```bash
git apply --check README_PHASE2_UPDATE.diff
git apply README_PHASE2_UPDATE.diff
```
