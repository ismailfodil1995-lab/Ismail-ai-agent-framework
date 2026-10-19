# test_pdf.py
from tools import run_tool

print("--- TESTING PDF TOOL DIRECTLY ---")
result = run_tool("read pdf sample-local-pdf.pdf")
print("RESULT:", result)