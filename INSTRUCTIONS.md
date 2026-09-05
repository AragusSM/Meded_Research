# MedVale RAG Lab: Step-by-Step Tester Guide

This guide assumes you are using Windows and have little or no programming experience.

## 1. Install Python

1. Go to <https://www.python.org/downloads/> and download Python 3.10 or newer for Windows.
2. Open the installer.
3. Check **Add Python to PATH** on the first screen.
4. Select **Install Now** and finish the installation.

## 2. Download the application

1. On the GitHub repository page, select the green **Code** button.
2. Select **Download ZIP**.
3. Right-click the downloaded ZIP and select **Extract All**.
4. Open the extracted folder. You should see `setup_windows.bat`, `run_windows.bat`, and `README.md`.

Git users may clone the repository instead.

## 3. Complete the one-time setup

1. Double-click `setup_windows.bat`.
2. If Windows asks whether to run it, confirm only if you downloaded it from the expected MedVale repository.
3. Wait while it creates a private Python environment and installs the required packages.
4. When **Setup complete** appears, press any key to close the window.

The first installation can take several minutes. Common setup problems are an old Python version, Python not being added to PATH, or no internet connection.

## 4. Start the application

1. Double-click `run_windows.bat`.
2. Keep the terminal window open while using the application.
3. Your browser should open <http://127.0.0.1:8090>.
4. The first launch prepares the bundled MedVale collections and may take longer than later launches.

`127.0.0.1` means the application is running on your own computer. It is not a public website.

## 5. Connect your model

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

- Stop: click the terminal window and press `Ctrl+C`.
- Restart later: double-click `run_windows.bat`.
- Refresh an outdated page after an upgrade: press `Ctrl+F5`.

## Troubleshooting

### The page cannot be reached

Make sure `run_windows.bat` is still open. Wait longer on the first launch, then refresh the page.

### API remains offline

- Recheck the provider, model name, and key.
- Check your internet connection and provider quota.
- For Ollama, confirm Ollama is running and the selected model is installed.

### Python was not found

Install Python again and select **Add Python to PATH** in its installer.

### Graph generation partially fails

Free services often enforce request limits. Try a smaller document, another available model, or retry later.

## Medical-content warning

This application is for research and studying. Do not use generated answers or questions to make patient-care decisions.
