import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
import app as app_module
from gemini_service import StudyAssistantError, _validate

LESSON = "Photosynthesis is how plants turn light, water and CO2 into sugar and oxygen."


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


class FakeAssistant:
    def run(self, task, text, n, language):
        if task == "flashcards":
            return [{"front": "a", "back": "b"}] * n, "fake"
        return "ok", "fake"


def test_index_loads(client):
    assert client.get("/").status_code == 200


def test_rejects_unknown_task(client):
    r = client.post("/api/study", json={"task": "hack", "text": LESSON})
    assert r.status_code == 400


def test_rejects_short_text(client):
    r = client.post("/api/study", json={"task": "explain", "text": "hi"})
    assert r.status_code == 400


def test_rejects_too_long(client):
    r = client.post("/api/study", json={"task": "explain", "text": "x" * 20000})
    assert r.status_code == 400


def test_success_and_count_clamped(client, monkeypatch):
    monkeypatch.setattr(app_module, "assistant", FakeAssistant())
    r = client.post("/api/study", json={"task": "flashcards", "text": LESSON, "count": 999})
    assert r.status_code == 200
    assert len(r.get_json()["result"]) == 15


def test_service_error_returns_502(client, monkeypatch):
    class Boom:
        def run(self, *a):
            raise StudyAssistantError("down")
    monkeypatch.setattr(app_module, "assistant", Boom())
    r = client.post("/api/study", json={"task": "explain", "text": LESSON})
    assert r.status_code == 502


def test_validate_quiz_ok_and_bad():
    good = [{"question": "q", "options": list("abcd"), "answer_index": 2, "explanation": "e"}]
    assert _validate("quiz", good) == good
    with pytest.raises(ValueError):
        _validate("quiz", [{"question": "q", "options": ["a"], "answer_index": 9, "explanation": "e"}])


def test_upload_txt(client):
    import io
    r = client.post("/api/upload", data={"file": (io.BytesIO(b"hello lesson text"), "a.txt")},
                    content_type="multipart/form-data")
    assert r.status_code == 200 and "hello" in r.get_json()["text"]


def test_upload_bad_type(client):
    import io
    r = client.post("/api/upload", data={"file": (io.BytesIO(b"x"), "a.exe")},
                    content_type="multipart/form-data")
    assert r.status_code == 400


def test_fallback_to_next_model(monkeypatch):
    import gemini_service as g, config

    class Boom(Exception):
        code = 504

    class Resp:
        text = '[{"front":"a","back":"b"}]'

    calls = []

    class Models:
        def generate_content(self, model, contents, config):
            calls.append(model)
            if model == "bad-model":
                raise Boom("timeout")
            return Resp()

    class Client:
        models = Models()

    monkeypatch.setattr(config, "GEMINI_MODEL", "bad-model")
    monkeypatch.setattr(config, "FALLBACK_MODELS", ["good-model"])
    monkeypatch.setattr(config, "DEMO_MODE", False)
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test")
    a = g.StudyAssistant(); a._client = Client()
    result, model = a.run("flashcards", "x" * 50, 1, "auto")
    assert model == "good-model" and calls[0] == "bad-model" and result[0]["front"] == "a"
