"""Run: python check_connection.py   -> tells you exactly what is wrong (DNS, network, key, model)."""
import os, socket, time
from dotenv import load_dotenv
load_dotenv()

HOST = "generativelanguage.googleapis.com"
print("1) DNS lookup ...", end=" ")
try:
    print("OK", socket.gethostbyname(HOST))
except Exception as e:
    print("FAILED:", e, "\n   FIX: set DNS to 8.8.8.8 / 8.8.4.4 or use a phone hotspot.")
    raise SystemExit(1)

print("2) TCP connect (port 443) ...", end=" ")
try:
    socket.create_connection((HOST, 443), timeout=10).close()
    print("OK")
except Exception as e:
    print("FAILED:", e, "\n   FIX: firewall/VPN/network blocks Google. Use a phone hotspot.")
    raise SystemExit(1)

key, model = os.getenv("GEMINI_API_KEY"), os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
if not key:
    print("3) API key ... MISSING. Put GEMINI_API_KEY in .env"); raise SystemExit(1)

print(f"3) Gemini call (model {model}) ...", end=" ")
try:
    from google import genai
    t = time.time()
    r = genai.Client(api_key=key).models.generate_content(model=model, contents="Say hi")
    print(f"OK ({time.time()-t:.1f}s):", r.text.strip()[:60])
    print("\nALL GOOD - run: python app.py")
except Exception as e:
    print("FAILED:", repr(e)[:300])
    print("   404 = change GEMINI_MODEL | 400/403 = new API key | 429 = wait, quota")
