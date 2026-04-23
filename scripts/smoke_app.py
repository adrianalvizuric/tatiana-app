"""Headless smoke test: run app.py through Streamlit's AppTest and assert no exceptions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from streamlit.testing.v1 import AppTest

def safe(s: str) -> str:
    return str(s).encode("ascii", "replace").decode("ascii")


at = AppTest.from_file("app.py", default_timeout=30).run()

print(f"exception count: {len(at.exception)}")
print(f"error count: {len(at.error)}")
print(f"titles: {len(at.title)}  headers: {len(at.header)}  buttons: {len(at.button)}")
print(f"first title: {safe(at.title[0].value) if at.title else '(none)'}")
print(f"button labels: {[safe(b.label) for b in at.button]}")

assert not at.exception, f"Exception raised: {[safe(str(e)) for e in at.exception]}"
print("\nOK: app booted without exception.")
