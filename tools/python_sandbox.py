import glob
import io
import os
import sys
from enum import Enum

BASE_DIR = "workspace"


class FileExtension(Enum):
    TXT = ".txt"
    MD = ".md"
    PY = ".py"
    JSON = ".json"
    CSV = ".csv"


def get_file_paths() -> list[str]:
    file_paths = glob.glob(f"{BASE_DIR}/**/*", recursive=True)
    relative_paths = [os.path.relpath(path, BASE_DIR) for path in file_paths]
    return relative_paths


def read_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        text = file.read()
        return text


def write_file(file_name: str, extension: FileExtension, text: str) -> str:
    file_path = f"{file_name}{extension.value}"

    with open(f"{BASE_DIR}/{file_path}", "w") as file:
        file.write(text)
        return "Success"


def execute_script_and_output_stdout(file_path: str) -> str:
    with open(f"{BASE_DIR}/{file_path}", "r") as file:
        script = file.read()
        try:
            output = io.StringIO()  # 標準出力をキャプチャする
            sys.stdout = output
            exec(script)
            result = output.getvalue()
            return f"Successfully executed the script. Output:\n{result}"
        except Exception as e:
            return f"An error occurred while evaluating the expression: {e}"
        finally:
            sys.stdout = sys.__stdout__  # 標準出力を元に戻す
