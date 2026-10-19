import datetime
import os
import re
from code_runner import run_python_code
from web_tool import scrape_url, search_google


def clean_target(target: str) -> str:
  """تنظيف أسماء الملفات أو الأوامر من الكلمات الملتصقة"""
  split_keywords = [
      r"\s+andthen\s+",
      r"\s+and then\s+",
      r"\s+then\s+",
      r"\s+after that\s+",
      r"\s+ثم\s+",
      r"\s+وبعدها\s+",
  ]
  for kw in split_keywords:
    target = re.split(kw, target, flags=re.IGNORECASE)[0].strip()
  return target.strip()


def run_tool(command: str):
  if not command or not command.strip():
    return None

  clean = command.strip()
  lower_cmd = clean.lower()

  # 1. البحث في الويب وسحب البيانات
  if lower_cmd.startswith("google search ") or lower_cmd.startswith("search "):
    query = clean_target(
        clean.replace("google search ", "").replace("search ", "")
    )
    return search_google(query)

  if lower_cmd.startswith("open website ") or lower_cmd.startswith("scrape "):
    url = clean_target(
        clean.replace("open website ", "").replace("scrape ", "")
    )
    return scrape_url(url)

  # 2. تشغيل الكود البرمجي
  if lower_cmd.startswith("run python ") or lower_cmd.startswith(
      "run script "
  ):
    filename = clean_target(
        clean.replace("run python ", "").replace("run script ", "")
    )
    return run_python_code(filename)

  # 3. إنشاء الملفات
  if lower_cmd.startswith("create file "):
    filename = clean_target(clean[12:])
    try:
      with open(filename, "w", encoding="utf-8") as f:
        if filename.endswith(".py"):
          f.write(
              f"# Auto-generated file: {filename}\nprint('Hello from"
              f" {filename}!')\n"
          )
        else:
          f.write("")
      return f"File '{filename}' created successfully."
    except Exception as e:
      return f"Error creating file '{filename}': {e}"

  # 4. قراءة الملفات
  if lower_cmd.startswith("read file "):
    filename = clean_target(clean[10:])
    if not os.path.exists(filename):
      return f"Error: File '{filename}' not found."
    try:
      with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
      return (
          f"Content of '{filename}':\n{content}"
          if content
          else f"File '{filename}' is empty."
      )
    except Exception as e:
      return f"Error reading file '{filename}': {e}"

  # 5. عرض الملفات
  if lower_cmd in ["list files", "show files"]:
    try:
      files = os.listdir(".")
      return (
          "Files in directory:\n" + "\n".join(f"- {f}" for f in files)
          if files
          else "Directory is empty."
      )
    except Exception as e:
      return f"Error listing files: {e}"

  # 6. الوقت والتاريخ والترحيب
  if lower_cmd == "time":
    return f"Current Time: {datetime.datetime.now().strftime('%H:%M:%S')}"

  if lower_cmd == "date":
    return f"Current Date: {datetime.datetime.now().strftime('%Y-%m-%d')}"

  if lower_cmd in ["hello", "hi"]:
    return "Hello! Agent system is active and ready for instructions."

  return None