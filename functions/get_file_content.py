import os
from google.genai import types

MAX_FILE_CHARS = 10000  # Max chars to read from a file


def get_file_content(working_directory, file_path):
    """
    Reads a file within the working_directory safely.
    Returns file contents (truncated if too long) or error string.
    """

    # Normalize paths
    working_directory_abs = os.path.abspath(working_directory)
    target_file_abs = os.path.abspath(os.path.join(working_directory, file_path))

    # 1. Validate scope
    if not target_file_abs.startswith(working_directory_abs):
        return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'

    # 2. Validate file exists
    if not os.path.isfile(target_file_abs):
        return f'Error: File not found or is not a regular file: "{file_path}"'

    try:
        with open(target_file_abs, "r", encoding="utf-8") as f:
            content = f.read()

        # 3. Truncate if too long
        if len(content) > MAX_FILE_CHARS:
            truncated_msg = (
                f'\n[...File "{file_path}" truncated at {MAX_FILE_CHARS} characters]'
            )
            content = content[:MAX_FILE_CHARS] + truncated_msg

        return content

    except Exception as e:
        return f"Error: {e}"


WORKING_DIR = r"C:\Users\Ash\Downloads\Coding Agent\Coding_Agent\calculator"

tests = [
    ("lorem.txt", "Truncation check"),
    ("main.py", "Valid file in root"),
    ("pkg/calculator.py", "Valid file in subdir"),
    ("/bin/cat", "Outside directory (should error)"),
    ("pkg/does_not_exist.py", "Non-existent file (should error)"),
]

for path, desc in tests:
    print(f"\n--- {desc} ({path}) ---")
    result = get_file_content(WORKING_DIR, path)
    print(result[:300] + "..." if len(result) > 300 else result)


# --- Gemini / LLM Function Schema ---
def make_function_schema(name, description, params):
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": params,
        },
    }


schema_get_file_content = make_function_schema(
    name="get_file_content",
    description=(
        "Reads the contents of a specified file within the working directory safely. "
        "Truncates the file at the configured maximum length to avoid sending too much data."
    ),
    params={
        "file_path": {
            "type": types.Type.STRING,
            "description": "The relative path of the file to read from the working directory.",
        },
        "working_directory": {
            "type": types.Type.STRING,
            "description": "The root directory that scopes file access. Files outside this directory are not allowed.",
        },
    },
)
