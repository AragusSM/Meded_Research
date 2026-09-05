# MedVale RAG Lab: Step-by-Step Tester Guide

This guide is written for Windows, macOS, and Linux testers with little or no programming experience.

## 1. Install Python

MedVale RAG Lab requires Python 3.10 or newer.

### Windows

1. Go to <https://www.python.org/downloads/windows/> and download Python 3.10 or newer.
2. Open the installer.
3. Check **Add Python to PATH** on the first screen.
4. Select **Install Now** and finish the installation.

### macOS

1. Go to <https://www.python.org/downloads/macos/> and download the current Python 3 installer.
2. Open the downloaded `.pkg` file and follow the installer.
3. Open **Terminal** from **Applications → Utilities**.
4. Run `python3 --version`. The result should be Python 3.10 or newer.

### Linux

Open a terminal and install Python, its virtual-environment support, and `pip` using your distribution's package manager.

Ubuntu, Debian, or Linux Mint:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

Fedora:

```bash
sudo dnf install python3 python3-pip
```

Then run `python3 --version` and confirm that it is Python 3.10 or newer. Package names may differ on other Linux distributions.

## 2. Download the application

1. On the GitHub repository page, select the green **Code** button.
2. Select **Download ZIP**.
3. Extract the downloaded ZIP. On Windows, right-click it and select **Extract All**. On macOS, double-click it. Most Linux file managers provide an **Extract Here** option.
4. Open the extracted folder. You should see `README.md`, `INSTRUCTIONS.md`, `requirements.txt`, and `run_app.py`.

Git users may clone the repository instead.

## 3. Complete the one-time setup

### Windows

1. Double-click `setup_windows.bat`.
2. If Windows asks whether to run it, confirm only if you downloaded it from the expected MedVale repository.
3. Wait while it creates a private Python environment and installs the required packages.
4. When **Setup complete** appears, press any key to close the window.

### macOS or Linux

1. Open **Terminal**.
2. Type `cd `, including the space, and drag the extracted MedVale RAG Lab folder into the Terminal window. Press **Return**. Linux users can instead right-click the folder and choose **Open in Terminal** when that option is available.
3. Run these commands one line at a time:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The prompt normally begins with `(.venv)` after activation. The first installation can take several minutes and requires an internet connection.

## 4. Start the application

### Windows

1. Double-click `run_windows.bat`.
2. Keep the terminal window open while using the application.
3. Your browser should open <http://127.0.0.1:8090>.
4. The first launch prepares the bundled MedVale collections and may take longer than later launches.

### macOS or Linux

1. Open **Terminal** in the extracted application folder as described in step 3.
2. Run these commands:

```bash
source .venv/bin/activate
python run_app.py
```

3. Keep the Terminal window open while using the application.
4. Open <http://127.0.0.1:8090> in a browser if it does not open automatically.
5. The first launch prepares the bundled MedVale collections and may take longer than later launches.

`127.0.0.1` means the application is running on your own computer. It is not a public website.

## 5. Connect your model

### Quick tested setup: Groq with GPT-OSS 120B

This project was tested with **Groq** (spelled with a `q`, not xAI's Grok) and the `openai/gpt-oss-120b` model.

1. Create or sign in to a GroqCloud account and open the [Groq API Keys page](https://console.groq.com/keys).
2. Select **Create API Key**, give it a recognizable name, and copy the key when it is shown.
3. Start MedVale RAG Lab and select the gear beside **API offline**.
4. Choose **Groq**. Keep the model as `openai/gpt-oss-120b` and the base URL as `https://api.groq.com/openai/v1`.
5. Paste the key and select **Verify and save**. The status should change to **API online**.

Groq explains key creation in its [official quickstart](https://console.groq.com/docs/quickstart) and lists `openai/gpt-oss-120b` in its [model documentation](https://console.groq.com/docs/model/openai/gpt-oss-120b). Free-tier availability and rate limits can change. Never put an API key in source code, `.env.example`, a Git commit, an issue, or a screenshot.

### Other providers

1. Find **API offline** in red at the upper-right corner.
2. Select the gear beside it.
3. Select Groq, Gemini, OpenRouter, OpenAI, Ollama, or Mock.
4. Confirm the model name. OpenRouter requires a specific model ID.
5. For an online provider, paste your own API key.
6. Select **Verify and save**.
7. Wait for **API online** in green.

The verifier sends a very small test request. A red status means the key, model, URL, provider access, local Ollama service, or internet connection needs attention.

The verified key is saved only in this browser's local storage. Use **Clear saved settings** in the gear dialog to remove it. Do not use a personal key on a shared or public computer.

## 6. Explore the built-in database

1. Open **Explore database**.
2. Select **MedVale IM · All Internal Medicine** or a chapter collection.
3. Select **Documents & chunks** to browse source passages and PDF pages.
4. Select **Graph** to explore concepts and relationships.
5. Left-drag to pan, right-drag to rotate, and use the mouse wheel to zoom.
6. Select a concept to see its description, properties, and top three source passages. Select **Show all** to reveal more.

The built-in database does not require an API for browsing. Answers and generated questions do.

## 7. Ask a question

1. Open **Build & Query**.
2. Select a collection and retrieval method.
3. Type a medical-study question.
4. Select **Answer question**.
5. Expand **Retrieved evidence** to inspect the supporting passages.

## 8. Generate a study question

1. Open **Questions**, then **Generate**.
2. Select a collection, retrieval method, and difficulty.
3. Enter a topic or learning objective.
4. Select **Generate question**.
5. Choose one answer and submit it to reveal the explanation and distractor rationales.
6. Use **Saved questions** to reopen earlier questions from that collection.

## 9. Build your own collection

1. Open **Build & Query**.
2. Enter a new collection name.
3. Select one or more PDF, DOCX, TXT, or Markdown files.
4. Leave **Create graph nodes and relationships** checked for graph generation. This requires a verified model.
5. Uncheck it if you only want the local document/vector baseline.
6. Select **Upload and build database** and keep the window open while it runs.

Uploaded files and generated databases remain under the local `data` folder and are not part of the repository.

## 10. Stop or restart

- Stop on any platform: select the terminal window and press `Ctrl+C`.
- Restart on Windows: double-click `run_windows.bat`.
- Restart on macOS or Linux: open Terminal in the application folder, run `source .venv/bin/activate`, and then run `python run_app.py`.
- Refresh an outdated page after an upgrade: press `Ctrl+F5` on Windows or Linux, or `Command+Shift+R` on macOS.

## Troubleshooting

### The page cannot be reached

Make sure the application terminal is still open and does not show an error. Wait longer on the first launch, then refresh the page.

### API remains offline

- Recheck the provider, model name, and key.
- Check your internet connection and provider quota.
- For Ollama, confirm Ollama is running and the selected model is installed.

### Python was not found

- Windows: install Python again and select **Add Python to PATH** in its installer.
- macOS or Linux: use `python3` to create the environment. After activating `.venv`, use `python` for the remaining commands.

### The virtual environment could not be created on Linux

On Ubuntu, Debian, or Linux Mint, run `sudo apt install python3-venv` and repeat the setup commands. Other distributions may provide virtual-environment support in a similarly named package.

### Graph generation partially fails

Free services often enforce request limits. Try a smaller document, another available model, or retry later.

## Medical-content warning

This application is for research and studying. Do not use generated answers or questions to make patient-care decisions.
