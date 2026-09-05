# MedVale RAG Lab

> [!IMPORTANT]
> **NEW TESTERS: START HERE → [Open the complete step-by-step installation and testing guide](INSTRUCTIONS.md)**
>
> It is written for people who do not code and includes Windows setup, API connection, built-in database use, question generation, custom document uploads, and troubleshooting.

MedVale RAG Lab is a local web application for building and evaluating medical retrieval systems. It compares document-order, vector, graph, and hybrid vector-plus-graph retrieval while keeping each tester's model credentials under their control.

The repository contains no MedVale game logic. It includes the standalone research application, tests, graph viewer, and the built-in MedVale internal-medicine knowledge base.

> Research and educational software only. Generated medical content can be incomplete or incorrect and must not be used for patient care.

## For testers

**Use the [step-by-step tester guide](INSTRUCTIONS.md) before installing or running the application.** Windows users can use the included setup and launch scripts without entering Python commands manually.

## Features

- Upload PDF, DOCX, TXT, and Markdown documents.
- Build a deterministic local TF-IDF vector index without an API.
- Generate document-grounded concept nodes, robust medical definitions, and typed edges using the tester's selected model.
- Compare document, vector, graph, and hybrid retrieval modes.
- Ask questions against a collection and inspect the retrieved evidence.
- Generate original NBME-style one-best-answer clinical vignettes with five homogeneous answer choices, explanations, distractor rationales, educational objectives, and source evidence.
- Reopen automatically saved generated questions.
- Explore graph nodes, relationships, source passages, and rendered source-PDF pages.
- Use the bundled MedVale internal-medicine graph and documents when no custom collection is available.

## Requirements

- Python 3.10 or newer
- A modern web browser
- Internet access when using a hosted API
- An API key for Groq, Gemini, OpenRouter, or OpenAI; alternatively, a local Ollama installation

The deterministic Mock provider needs no key and is intended only for interface testing.

## Quick start

### Windows

1. Double-click `setup_windows.bat` once.
2. Double-click `run_windows.bat` whenever you want to use the application.
3. Open <http://127.0.0.1:8090> if the browser does not open automatically.
4. Select the gear beside **API offline**, enter your provider settings, and choose **Verify and save**.

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_app.py
```

Then open <http://127.0.0.1:8090>.

## API providers

### Fastest tested setup: Groq with GPT-OSS 120B

This project was tested with **Groq** (spelled with a `q`, not xAI's Grok) and the `openai/gpt-oss-120b` model.

1. Create or sign in to a GroqCloud account and open the [Groq API Keys page](https://console.groq.com/keys).
2. Select **Create API Key**, give it a recognizable name, and copy the key when it is shown.
3. Start MedVale RAG Lab and select the gear beside **API offline**.
4. Choose **Groq**. Keep the model as `openai/gpt-oss-120b` and the base URL as `https://api.groq.com/openai/v1`.
5. Paste the key and select **Verify and save**. The status should change to **API online**.

Groq documents the key-creation process in its [official quickstart](https://console.groq.com/docs/quickstart) and lists `openai/gpt-oss-120b` in its [official model documentation](https://console.groq.com/docs/model/openai/gpt-oss-120b). Free-tier availability and rate limits can change. Never paste a key into source code, `.env.example`, a Git commit, an issue, or a screenshot.

### Other supported providers

The web interface supports:

| Provider | Default or example model | Key required |
|---|---|---|
| Groq | `openai/gpt-oss-120b` | Yes |
| Gemini | `gemini-2.5-flash` | Yes |
| OpenRouter | Tester chooses a model ID | Yes |
| OpenAI | `gpt-5-mini` | Yes |
| Ollama | `qwen3:14b` | No, but Ollama and the model must be installed locally |
| Mock | `deterministic-mock` | No |

The status remains **API offline** until the application successfully sends a small verification request to the chosen model. Changing a provider, model, URL, or key requires verification again.

Verified browser settings—including the API key—are stored in that browser's local storage so they survive an application restart. They are not written to a collection, `.env`, log, or server-side database. This approach is intended for local testing. A publicly hosted deployment should replace it with an encrypted credential store or provider OAuth and must use HTTPS.

## Collections and local data

On the first run, the application imports the canonical files in `bundled_data/` into generated collections under `data/`. This can take a little time. The `data/` directory is intentionally ignored by Git because it also contains tester uploads, generated indexes, SQLite run history, and saved questions.

Built-in collections include all internal medicine plus individual chapter/module collections. They work for document browsing, graph exploration, and local retrieval without generating another graph. Natural-language answers and generated questions still require a verified model.

## Developer setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest tests -q
python -m medrag.api
```

Configuration defaults can be copied from `.env.example`, but browser users should configure model credentials through the gear. Never commit `.env` or real credentials.

## Architecture

- `medrag/api.py`: Flask routes and provider verification
- `medrag/indexing.py`: document chunking, local vector indexing, and graph extraction
- `medrag/retrieval.py`: document/vector/graph/hybrid retrieval
- `medrag/service.py`: answer and clinical-question generation
- `medrag/database.py`: per-collection SQLite schema and run history
- `medrag/static/` and `medrag/templates/`: browser interface and graph explorer
- `bundled_data/`: canonical MedVale internal-medicine database and source PDFs
- `tests/`: smoke and integration tests

## Research behavior

- Graph extraction is constrained to supplied document chunks.
- Every generated node and edge requires a verbatim supporting quote.
- Node descriptions are prompted as standalone, document-grounded medical definitions; relationship claims belong on edges.
- All graph collections use the interoperable `medivale_graph_v1` schema.
- Answering may use model background knowledge but is instructed to distinguish it from retrieved evidence.
- Question generation follows NBME one-best-answer construction principles. NBME and UWorld are style references only; generated items must be original.
- Responses, evidence, provider/model identifiers, and experimental parameters are saved in the selected collection for reproducibility. API keys are not included in that history.

## Running the tests

```bash
python -m pytest tests -q
```

## Stopping the application

Return to the terminal window running MedVale RAG Lab and press `Ctrl+C`.

## Known limitations

- TF-IDF provides a deterministic experimental vector baseline, not a neural embedding model.
- Free API tiers may impose rate limits during large graph builds.
- The bundled MedVale nodes contain curated descriptions; they do not all contain dictionary-style definitions.
- Browser-local API-key storage is appropriate for local testing but not the recommended production credential design.
