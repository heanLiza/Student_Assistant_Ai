import re
from pathlib import Path

# emoji, pictographs, flags, arrows and dingbat symbols (Khmer text is not affected)
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2190-\u21FF\u2300-\u23FF\uFE0F]")

for name in ["templates/index.html", "static/app.js", "static/style.css"]:
    f = Path(name)
    text = f.read_text(encoding="utf-8")
    found = EMOJI.findall(text)
    f.write_text(EMOJI.sub("", text), encoding="utf-8")
    print(f"{name}: removed {len(found)} -> {''.join(sorted(set(found))) or 'none'}")