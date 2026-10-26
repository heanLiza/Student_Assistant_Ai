# Study Assistant — Narrow AI Application (Gemini API)

**Topic 12: Study Assistant** · កិច្ចការផ្ទះ៖ បង្កើត Narrow AI Application ដោយប្រើ Chatbot API

## 1. Project description / ការពិពណ៌នា
Study Assistant គឺជា **Narrow AI** ដែលជួយសិស្ស/និស្សិតតែក្នុងការសិក្សា ប៉ុណ្ណោះ (មិនឆ្លើយសំណួរក្រៅការសិក្សា)។

| Feature | Description |
|---|---|
| ពន្យល់មេរៀន | Explain the lesson step by step with examples |
| សង្ខេបមេរៀន | 5–8 bullet summary + key takeaway |
| Flashcards | Click-to-flip cards |
| Quiz | Multiple choice, instant feedback, score, explanation |
| សំណួរហាត់ | Practice questions with model answer + explanation |

- **AI Platform:** Google Gemini API (`google-genai` SDK, model `gemini-3.8-flash`)
- **Backend:** Python + Flask  ·  **Frontend:** HTML / CSS / JavaScript

## 2. Team roles / តួនាទី
| Member | Role |
|---|---|
| (name) | Team Leader |
| (name) | UI/UX Designer |
| **(your name)** | **Programmer / Developer** |
| (name) | AI Prompt & API Developer |
| (name) | Tester / Documentation |

**Programmer/Developer responsibilities done:** Flask backend, Gemini API integration, input validation,
output validation (JSON schema check), retries/error handling, secure API-key handling, UI wiring, unit tests.

## 3. Project structure
```
study-assistant/
├── app.py              # Flask routes + request validation
├── gemini_service.py   # Gemini API call, retries, output validation
├── prompts.py          # System prompt + task prompt templates
├── config.py           # Settings (key loaded from environment)
├── templates/index.html
├── static/style.css
├── static/app.js       # UI logic: tabs, flashcards, quiz, practice
├── tests/test_app.py   # Automated tests
├── requirements.txt
├── .env.example        # Template for the secret key (copy to .env)
└── .gitignore          # Keeps .env out of Git
```

## 4. Installation & run / របៀបដំឡើង
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env
# open .env and paste your NEW Gemini API key
python app.py
```
Open **http://127.0.0.1:5000** in the browser.
Get a key at https://aistudio.google.com/apikey

## 5. API key security / សុវត្ថិភាព API Key
- Key is stored only in `.env` (listed in `.gitignore`) and read via `os.getenv`.
- The key is never sent to the browser; the browser only calls our own `/api/study`.
- Never paste the key into a terminal, screenshot, chat or GitHub. If leaked → delete it and create a new one.
- Detailed technical errors stay in the server log; users see only a safe message.

## 6. Prompt design (Narrow AI)
- **System prompt** limits the bot to study tasks, forces it to use only the given lesson, forbids
  invented facts, and treats lesson text as data (basic prompt-injection defense).
- **Task prompts** per feature; flashcards/quiz/practice request **JSON only** with an exact schema.
- `response_mime_type="application/json"` + server-side schema validation → UI never breaks on bad output.
- Output language: Auto (same as lesson) / Khmer / English.

## 7. Input / Output management
| Layer | Rule |
|---|---|
| Input | 20–15,000 characters, known task + language only, item count clamped to 1–15 |
| Output (text) | Rendered with `textContent` (no HTML injection) |
| Output (JSON) | Validated: required fields, exactly 4 options, `answer_index` 0–3 |
| Failure | 3 retries with backoff → friendly error (HTTP 502) |

## 8. Testing / ការធ្វើតេស្ត
Automated: `python -m pytest -q` → 7 tests (page loads, bad task, short text, too-long text,
count clamping, service-failure handling, quiz schema validation).

Manual test cases (fill in results with real Gemini):
| # | Test | Expected | Result |
|---|---|---|---|
| 1 | Khmer lesson → Explain | Khmer explanation | |
| 2 | English lesson → Summarize | Bullets + key takeaway | |
| 3 | Flashcards ×5 | 5 flip cards | |
| 4 | Quiz ×5, answer all | Correct/wrong colors, explanation, score | |
| 5 | Practice ×5 | Reveal answer works | |
| 6 | Non-study text ("write me a love poem") | Polite refusal | |
| 7 | Empty / 5-char input | Error message, no API call | |
| 8 | Wrong API key | "AI could not answer" message, no crash | |
| 9 | Disconnect internet | Error message, button re-enabled | |

## 9. Known limitations / future work
- No login/history; no PDF upload (could add file parsing); in-memory only.
- Add rate limiting before public deployment; run behind gunicorn instead of `python app.py`.
