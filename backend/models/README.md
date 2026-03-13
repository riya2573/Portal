# Models Directory

GGUF model files are stored here.

## Auto-Download

The model **auto-downloads on first run** when you start the backend.
Just run `uvicorn main:app --reload --port 8000` and wait (~4.6GB download).

## Manual Download

If auto-download fails, run this in the `backend` folder:

```python
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='bartowski/Meta-Llama-3.1-8B-Instruct-GGUF',
    filename='Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf',
    local_dir='./models'
)
"
```

## Alternative Models

For systems with less RAM:
- `Meta-Llama-3.1-8B-Instruct-Q3_K_M.gguf` (~3.5 GB)
- `Meta-Llama-3.1-8B-Instruct-Q2_K.gguf` (~2.8 GB)

## Note

GGUF files are large and excluded from git via `.gitignore`.
