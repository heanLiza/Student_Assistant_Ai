"""Gemini API layer: model fallback, timeouts, JSON validation, clear errors."""
import json
import time

from google import genai
from google.genai import types

import config
from prompts import SYSTEM_PROMPT, build_prompt


class StudyAssistantError(Exception):
    """Error that is safe to show to the user."""


def _validate(task: str, data) -> list:
    if not isinstance(data, list) or not data:
        raise ValueError("expected a non-empty list")
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("bad item")
        if task == "flashcards":
            ok = isinstance(item.get("front"), str) and isinstance(item.get("back"), str)
        elif task == "quiz":
            opts, idx = item.get("options"), item.get("answer_index")
            ok = (isinstance(item.get("question"), str) and isinstance(opts, list) and len(opts) == 4
                  and isinstance(idx, int) and 0 <= idx <= 3 and isinstance(item.get("explanation"), str))
        else:
            ok = all(isinstance(item.get(k), str) for k in ("question", "answer", "explanation"))
        if not ok:
            raise ValueError("item has wrong shape")
    return data


def explain_error(err) -> str:
    text = repr(err)
    code = getattr(err, "code", None)
    if "getaddrinfo" in text or "11001" in text:
        return "DNS error: set DNS to 8.8.8.8 / 8.8.4.4 or use a phone hotspot."
    if "Timeout" in text or "timed out" in text or code == 504:
        return "Gemini took too long (network slow). Try a shorter text, fewer items, or a phone hotspot."
    if "Connect" in text:
        return "Cannot connect to Gemini. Check internet, VPN, firewall, or use a phone hotspot."
    hints = {400: "API key invalid or bad request. Check GEMINI_API_KEY.",
             401: "API key invalid. Create a new key in Google AI Studio.",
             403: "API key blocked. Create a new key in Google AI Studio.",
             404: "Model not found. Run: python find_model.py",
             429: "Quota exceeded. Wait a minute and try again.",
             503: "Gemini is overloaded. Try again in a minute."}
    return hints.get(code, "The AI could not answer. See the server terminal for details.")


def _demo(task: str, n: int):
    if task == "explain":
        return "[DEMO MODE] Sample text only. Set DEMO_MODE=0 in .env for real AI."
    if task == "summarize":
        return "- [DEMO] Sample point one\n- [DEMO] Sample point two\nKey takeaway: demo data."
    if task == "flashcards":
        return [{"front": f"[DEMO] Term {i+1}", "back": f"Definition {i+1}"} for i in range(n)]
    if task == "quiz":
        return [{"question": f"[DEMO] Question {i+1}?", "options": ["A1", "B1", "C1", "D1"],
                 "answer_index": 1, "explanation": "Demo explanation."} for i in range(n)]
    return [{"question": f"[DEMO] Practice {i+1}?", "answer": "Demo answer",
             "explanation": "Demo explanation."} for i in range(n)]


class StudyAssistant:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if not config.GEMINI_API_KEY:
            raise StudyAssistantError("Missing GEMINI_API_KEY. Put your key in the .env file.")
        if self._client is None:
            self._client = genai.Client(
                api_key=config.GEMINI_API_KEY,
                http_options=types.HttpOptions(timeout=config.PER_CALL_TIMEOUT_MS),
            )
        return self._client

    def _models(self):
        names = [config.GEMINI_MODEL]
        names += [m for m in config.FALLBACK_MODELS if m not in names]
        return names

    def _configs(self, as_json: bool):
        """Fast config first (no 'thinking', capped length); plain config as backup."""
        base = dict(system_instruction=SYSTEM_PROMPT, temperature=0.4,
                    max_output_tokens=config.MAX_OUTPUT_TOKENS,
                    response_mime_type="application/json" if as_json else "text/plain")
        yield types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=0), **base)
        yield types.GenerateContentConfig(**base)

    def run(self, task: str, text: str, n: int, language: str):
        """Returns (result, model_name)."""
        if config.DEMO_MODE:
            return _demo(task, n), "demo"
        client = self._get_client()
        prompt = build_prompt(task, text[:config.MODEL_INPUT_CHARS], n, config.LANGUAGES[language])
        as_json = task in config.JSON_TASKS
        start, last_error = time.time(), None

        for model in self._models():
            for cfg in self._configs(as_json):
                if time.time() - start > config.TOTAL_BUDGET_SECONDS:
                    raise StudyAssistantError(explain_error(last_error))
                try:
                    resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
                    out = (resp.text or "").strip()
                    if not out:
                        raise ValueError("empty response")
                    return (_validate(task, json.loads(out)) if as_json else out), model
                except Exception as e:
                    last_error = e
                    print(f"[gemini] {model} failed: {e!r}"[:400])
                    code = getattr(e, "code", None)
                    if code in (401, 403):      # key problem: other models cannot help
                        raise StudyAssistantError(explain_error(e))
                    if code != 400:             # 400 may mean 'thinking not supported' -> try plain config
                        break                   # otherwise go to the next model
        raise StudyAssistantError(explain_error(last_error))
