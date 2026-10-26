"""Flask web app: UI, /api/study (AI) and /api/upload (drag & drop files)."""
import io
import time

from flask import Flask, jsonify, render_template, request

import config
from gemini_service import StudyAssistant, StudyAssistantError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_BYTES
assistant = StudyAssistant()


@app.get("/")
def index():
    return render_template("index.html", max_chars=config.MAX_INPUT_CHARS, demo=config.DEMO_MODE)


@app.post("/api/study")
def study():
    body = request.get_json(silent=True) or {}
    task = body.get("task")
    text = str(body.get("text", "")).strip()
    language = body.get("language", "auto")
    try:
        n = int(body.get("count", config.DEFAULT_ITEMS))
    except (TypeError, ValueError):
        n = config.DEFAULT_ITEMS

    if task not in config.TASKS:
        return jsonify(error="Unknown task."), 400
    if language not in config.LANGUAGES:
        return jsonify(error="Unknown language."), 400
    if len(text) < config.MIN_INPUT_CHARS:
        return jsonify(error=f"Please enter at least {config.MIN_INPUT_CHARS} characters."), 400
    if len(text) > config.MAX_INPUT_CHARS:
        return jsonify(error=f"Text is too long (max {config.MAX_INPUT_CHARS} characters)."), 400
    n = max(config.MIN_ITEMS, min(n, config.MAX_ITEMS))

    t0 = time.time()
    try:
        result, model = assistant.run(task, text, n, language)
    except StudyAssistantError as e:
        return jsonify(error=str(e)), 502
    return jsonify(task=task, result=result, model=model, seconds=round(time.time() - t0, 1),
                   truncated=len(text) > config.MODEL_INPUT_CHARS)


@app.post("/api/upload")
def upload():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(error="No file."), 400
    name, data = f.filename.lower(), f.read()
    try:
        if name.endswith((".txt", ".md", ".csv")):
            text = data.decode("utf-8", errors="ignore")
        elif name.endswith(".pdf"):
            from pypdf import PdfReader
            text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
        elif name.endswith(".docx"):
            import docx
            text = "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)
        else:
            return jsonify(error="Supported files: .txt .md .pdf .docx"), 400
    except ImportError:
        return jsonify(error="Run: pip install pypdf python-docx"), 500
    except Exception:
        return jsonify(error="Could not read this file."), 400
    text = text.strip()
    if not text:
        return jsonify(error="No readable text found (scanned PDF?)."), 400
    return jsonify(text=text[:config.MAX_INPUT_CHARS], full_length=len(text))


@app.errorhandler(413)
def too_big(_):
    return jsonify(error="File too large (max 5 MB)."), 413


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8765)
