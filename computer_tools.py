import os
import fitz  # PyMuPDF
import pandas as pd

BASE_DIR = os.getcwd()


def _safe_path(path):
    return os.path.abspath(os.path.join(BASE_DIR, path))


# =====================================
# Files
# =====================================

def create_file(filename):

    try:

        path = _safe_path(filename)

        os.makedirs(os.path.dirname(path), exist_ok=True)

        if os.path.exists(path):
            return f"File '{filename}' already exists."

        with open(path, "w", encoding="utf-8"):
            pass

        return f"File '{filename}' created successfully."

    except Exception as e:
        return str(e)


def read_file(filename):

    try:

        path = _safe_path(filename)

        if not os.path.exists(path):
            return "File not found."

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    except Exception as e:
        return str(e)


def write_file(filename, content):

    try:

        path = _safe_path(filename)

        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Written successfully to '{filename}'."

    except Exception as e:
        return str(e)


def append_file(filename, content):

    try:

        path = _safe_path(filename)

        with open(path, "a", encoding="utf-8") as f:
            f.write(content)

        return f"Content appended to '{filename}'."

    except Exception as e:
        return str(e)


def delete_file(filename):

    try:

        path = _safe_path(filename)

        if not os.path.exists(path):
            return "File not found."

        os.remove(path)

        return f"Deleted '{filename}'."

    except Exception as e:
        return str(e)


def rename_file(old_name, new_name):

    try:

        old_path = _safe_path(old_name)
        new_path = _safe_path(new_name)

        if not os.path.exists(old_path):
            return "File not found."

        os.rename(old_path, new_path)

        return f"Renamed '{old_name}' to '{new_name}'."

    except Exception as e:
        return str(e)


def list_files(folder="."):

    try:

        path = _safe_path(folder)

        if not os.path.exists(path):
            return "Folder not found."

        files = os.listdir(path)

        if not files:
            return "Folder is empty."

        return "\n".join(sorted(files))

    except Exception as e:
        return str(e)


# =====================================
# PDF
# =====================================

def read_pdf(filename):

    try:

        path = _safe_path(filename)

        if not os.path.exists(path):
            return "PDF not found."

        doc = fitz.open(path)

        text = ""

        for page in doc:
            text += page.get_text()

        doc.close()

        return text.strip()

    except Exception as e:
        return str(e)


# =====================================
# Excel
# =====================================

def read_excel(filename):

    try:

        path = _safe_path(filename)

        if not os.path.exists(path):
            return "Excel file not found."

        df = pd.read_excel(path)

        return df.to_string(index=False)

    except Exception as e:
        return str(e)


# =====================================
# CSV
# =====================================

def read_csv(filename):

    try:

        path = _safe_path(filename)

        if not os.path.exists(path):
            return "CSV file not found."

        df = pd.read_csv(path)

        return df.to_string(index=False)

    except Exception as e:
        return str(e)