import os


def create_file(filename):

    try:
        with open(filename, "w", encoding="utf-8") as f:
            pass

        return f"File '{filename}' created successfully."

    except Exception as e:
        return str(e)


def read_file(filename):

    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()

    except Exception as e:
        return str(e)


def list_files():

    files = os.listdir()

    if not files:
        return "Folder is empty."

    return "\n".join(files)