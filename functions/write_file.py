import os
from google.genai import types


def write_file(working_directory, file_path, content):
    """
    Safely writes to a file within working_directory.
    Creates the file if it doesn't exist.
    Returns success message or error string.
    """

    # Normalize paths
    working_directory_abs = os.path.abspath(working_directory)
    target_file_abs = os.path.abspath(os.path.join(working_directory, file_path))

    # 1. Validate scope
    if not target_file_abs.startswith(working_directory_abs):
        return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'

    # 2. Ensure parent directories exist
    try:
        parent_dir = os.path.dirname(target_file_abs)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
    except Exception as e:
        return f"Error: Failed to create directories for {file_path}: {e}"

    # 3. Write the content
    try:
        with open(target_file_abs, "w", encoding="utf-8") as f:
            f.write(content)
        return (
            f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
        )
    except Exception as e:
        return f"Error: Failed to write to {file_path}: {e}"


# --- Schema for Gemini / LLM function calling ---
def make_function_schema(name, description, params):
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": params,
        },
    }


schema_write_file = make_function_schema(
    name="write_file",
    description=(
        "Safely writes the provided content to a file within the working directory. "
        "Creates the file and any missing directories if necessary. "
        "Returns a success or error message."
    ),
    params={
        "file_path": {
            "type": types.Type.STRING,
            "description": "The relative path of the file to write inside the working directory.",
        },
        "working_directory": {
            "type": types.Type.STRING,
            "description": "The root directory that scopes file writes. Files outside this directory are not allowed.",
        },
        "content": {
            "type": types.Type.STRING,
            "description": "The content to write into the file.",
        },
    },
)


# --- Example tests ---
if __name__ == "__main__":
    WORKING_DIR = r"C:\Users\Ash\Downloads\Coding Agent\Coding_Agent\calculator"

    tests = [
        ("lorem.txt", "wait, this isn't lorem ipsum"),
        ("pkg/morelorem.txt", "lorem ipsum dolor sit amet"),
        ("/tmp/temp.txt", "this should not be allowed"),
    ]

    for file_path, content in tests:
        print(f"\n--- Writing to {file_path} ---")
        result = write_file(WORKING_DIR, file_path, content)
        print(result)
