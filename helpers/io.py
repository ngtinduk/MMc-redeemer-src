import __main__
import os
import json
# import sys

# if getattr(sys, "frozen", False):
#     ROOT_PATH = os.path.dirname(sys.executable)
# else:
#     ROOT_PATH = os.path.abspath(os.path.dirname(__main__.__file__))

# ROOT_PATH = os.path.abspath(os.path.dirname(__main__.__file__))
# ROOT_PATH = os.path.abspath(os.path.dirname(sys.executable))

ROOT_PATH = "."

def load_json(file_path: str) -> dict | list:
    full_file_path = f"{ROOT_PATH}\\{file_path}"

    if not os.path.isfile(full_file_path):
        dirs = file_path.split("\\")[:-1]

        os.makedirs(ROOT_PATH + "\\" + "\\".join(dirs), exist_ok=True)

    with open(full_file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def overwrite_json(file_path: str, content: dict | list) -> None:
    full_file_path = f"{ROOT_PATH}\\{file_path}"

    if not os.path.isfile(full_file_path):
        dirs = file_path.split("\\")[:-1]

        os.makedirs(ROOT_PATH + "\\" + "\\".join(dirs), exist_ok=True)

    with open(full_file_path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=4)


def read_lines(file_path: str) -> list[str]:
    full_file_path = f"{ROOT_PATH}\\{file_path}"

    if not os.path.isfile(full_file_path):
        dirs = file_path.split("\\")[:-1]

        os.makedirs(ROOT_PATH + "\\" + "\\".join(dirs), exist_ok=True)

        open(full_file_path, "w", encoding="utf-8").close()

        return []

    with open(full_file_path, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def append_line(file_path: str, line: str) -> None:
    full_file_path = f"{ROOT_PATH}\\{file_path}"

    if not os.path.isfile(full_file_path):
        dirs = file_path.split("\\")[:-1]

        os.makedirs(ROOT_PATH + "\\" + "\\".join(dirs), exist_ok=True)

    with open(f"{ROOT_PATH}\\{file_path}", "a", encoding="utf-8") as f:
        f.write(f"{line}\n")


def remove_line(file_path: str, line: str) -> None:
    full_file_path = f"{ROOT_PATH}\\{file_path}"

    if not os.path.isfile(full_file_path):
        dirs = file_path.split("\\")[:-1]

        os.makedirs(ROOT_PATH + "\\" + "\\".join(dirs), exist_ok=True)

    with open(full_file_path, "r", encoding="utf-8") as f:
        content = f.read().splitlines()

    if not line in content:
        return

    content.remove(line)

    with open(full_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(content))


def overwrite_file(file_path: str, content: str) -> None:
    full_file_path = f"{ROOT_PATH}\\{file_path}"

    if not os.path.isfile(full_file_path):
        dirs = file_path.split("\\")[:-1]

        os.makedirs(ROOT_PATH + "\\" + "\\".join(dirs), exist_ok=True)

    with open(full_file_path, "w", encoding="utf-8") as f:
        f.write(content)
