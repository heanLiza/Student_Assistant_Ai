"""Run: python find_model.py  -> tests models with a tiny prompt, shows speed, saves the fastest to .env"""
import os, re, time
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"), http_options=types.HttpOptions(timeout=20000))
try:
    names = [m.name.replace("models/", "") for m in client.models.list()]
except Exception as e:
    raise SystemExit(f"Cannot list models: {e!r}\nFix network/key first: python check_connection.py")
cands = ["gemini-flash-latest", "gemini-flash-lite-latest"] + [n for n in names if "flash" in n and "image" not in n and "tts" not in n]
seen, results = set(), []
for n in cands:
    if n in seen: continue
    seen.add(n)
    if len(seen) > 8: break
    t = time.time()
    try:
        client.models.generate_content(model=n, contents="Say hi")
        dt = time.time() - t
        print(f"OK    {n:40s} {dt:.1f}s"); results.append((dt, n))
    except Exception as e:
        print(f"FAIL  {n:40s} {repr(e)[:80]}")
if not results:
    raise SystemExit("No model worked. Check key/network.")
best = min(results)[1]
env = open(".env", encoding="utf-8").read() if os.path.exists(".env") else ""
env = re.sub(r"^GEMINI_MODEL=.*\n?", "", env, flags=re.M).rstrip("\n") + f"\nGEMINI_MODEL={best}\n"
open(".env", "w", encoding="utf-8").write(env)
print(f"\nSaved GEMINI_MODEL={best} to .env  -> now run: python app.py")
