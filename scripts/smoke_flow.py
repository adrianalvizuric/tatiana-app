"""Click through welcome -> home, verify post-welcome view renders without errors.

Note: this writes `first_seen_at` to the real Sheet. Run once; afterward the
welcome screen won't show until you clear that state row.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from streamlit.testing.v1 import AppTest


def safe(s: str) -> str:
    return str(s).encode("ascii", "replace").decode("ascii")


at = AppTest.from_file("app.py", default_timeout=30).run()
print("== initial load ==")
print(f"buttons: {[safe(b.label) for b in at.button]}  exceptions: {len(at.exception)}")

if at.button and "????????" not in safe(at.button[0].label):  # welcome button still visible
    at.button[0].click().run()
    print("\n== after welcome click ==")

print(f"titles: {[safe(t.value) for t in at.title]}")
print(f"headers: {[safe(h.value) for h in at.header]}")
print(f"buttons: {[safe(b.label) for b in at.button]}")
print(f"info messages: {[safe(i.value) for i in at.info]}")
print(f"exceptions: {len(at.exception)}")

assert not at.exception, f"Exception raised: {[safe(str(e)) for e in at.exception]}"
print("\nOK: post-welcome view rendered without exception.")
