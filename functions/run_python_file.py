import os
import subprocess
from google.genai import types


def run_python_file(working_directory, file_path, args=[]):
    """
    Safely executes a Python file within the working_directory.
    Captures stdout and stderr, enforces a 30-second timeout.
    Returns formatted output or error string.
    """

    # Normalize paths
    working_directory_abs = os.path.abspath(working_directory)
    target_file_abs = os.path.abspath(os.path.join(working_directory, file_path))

    # 1. Validate scope
    if not target_file_abs.startswith(working_directory_abs):
        return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

    # 2. Validate file existence
    if not os.path.isfile(target_file_abs):
        return f'Error: File "{file_path}" not found.'

    # 3. Validate Python file
    if not target_file_abs.endswith(".py"):
        return f'Error: "{file_path}" is not a Python file.'

    try:
        completed = subprocess.run(
            ["python", target_file_abs, *args],
            capture_output=True,
            text=True,
            cwd=working_directory_abs,
            timeout=30,
        )

        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        output = ""

        if stdout:
            output += f"STDOUT:\n{stdout}\n"
        if stderr:
            output += f"STDERR:\n{stderr}\n"
        if completed.returncode != 0:
            output += f"Process exited with code {completed.returncode}\n"
        if not stdout and not stderr:
            output = "No output produced."

        return output.strip()

    except Exception as e:
        return f"Error: executing Python file: {e}"


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


schema_run_python_file = make_function_schema(
    name="run_python_file",
    description=(
        "Executes a Python file within the working directory safely, capturing stdout and stderr. "
        "Timeout of 30 seconds is enforced. Returns output or error messages."
    ),
    params={
        "file_path": {
            "type": types.Type.STRING,
            "description": "The relative path of the Python file to execute.",
        },
        "working_directory": {
            "type": types.Type.STRING,
            "description": "The root directory that scopes Python file execution.",
        },
        "args": {
            "type": types.Type.ARRAY,
            "description": "Optional list of command-line arguments to pass to the Python script.",
        },
    },
)
