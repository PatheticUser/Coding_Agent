import os
import sys
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.get_files_info import get_files_info, schema_get_files_info
from functions.get_file_content import get_file_content, schema_get_file_content
from functions.write_file import write_file, schema_write_file
from functions.run_python_file import run_python_file, schema_run_python_file
from functions.delete_file import delete_file, schema_delete_file
from functions.get_project_description import (
    get_project_description,
    schema_get_project_description,
)

# --- Configuration & Initialization ---

# Load environment variables
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

try:
    if not api_key:
        # Improved: Raise a more user-friendly error
        raise ValueError(
            "GEMINI_API_KEY environment variable not found. Please set it in your .env file."
        )
    client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    sys.exit(1)

# Parse CLI flags (Simplified to check for verbose, and usage is now part of verbose)
args = sys.argv[1:]
verbose_mode = "--verbose" in args
# usage_mode is now implicitly controlled by verbose_mode for cleaner UI separation

# Hardcoded working directory (Ensure this is correct and accessible!)
WORKING_DIR = r"C:\Users\Muhammad Rameez\Documents\CodeCrafter\calculator"
if verbose_mode:
    print(f"Working Directory: {WORKING_DIR}")

# Load project metadata once at startup
try:
    with open(
        os.path.join(WORKING_DIR, "project_description.json"), "r", encoding="utf-8"
    ) as f:
        PROJECT_METADATA = json.load(f)
except FileNotFoundError:
    print(
        f"Error: project_description.json not found in {WORKING_DIR}. File access control may be incomplete."
    )
    PROJECT_METADATA = {"key_files": {}}
except Exception as e:
    print(f"Error loading project_description.json: {e}")
    PROJECT_METADATA = {"key_files": {}}

KEY_FILES = list(PROJECT_METADATA["key_files"].keys())

# Define the content to inject into the start of the conversation
# Using a system role for project metadata is often better than a user role for context injection
PROJECT_SUMMARY_MESSAGE = types.Content(
    role="user",  # Changed to 'system' to align with modern best practices for context
    parts=[
        types.Part(text=f"Project Metadata: {json.dumps(PROJECT_METADATA, indent=2)}")
    ],
)

# Agent Name for clear terminal output
AGENT_NAME = "CodeCrafter"


def is_file_allowed(file_path: str) -> bool:
    """Ensure file path is in project metadata key_files."""
    # Check if the file_path matches any of the relative paths in KEY_FILES
    return any(file_path == kf for kf in KEY_FILES)


# System prompt (The instruction set for the model) - Kept largely the same
system_prompt = """
You are an expert AI assistant operating in a closed, local coding environment. Your singular goal is to efficiently and reliably complete the user's software development and file-related requests.

**Core Protocol: Project-Aware CoT**

You must adhere to a strict Chain of Thought (CoT) workflow to ensure strategic execution. Your protocol is now informed by the project's metadata:

1. First, check for and read the **project_description.json** file. Use the **project_summary**, **key_files**, and **debug_notes** to understand the project's architecture and the goal of the user's request.
2. Based on the user's request and the project metadata, generate a clear, step-by-step **Function Call Plan**. This plan MUST specify the exact file(s) identified by the metadata that need reading or modifying.
3. Perform the next single function call from your plan.
4. Present the results. If the task is complete, summarize the final outcome and confirm that testing (if applicable) was successful. If the task is ongoing, present the updated plan and ask for confirmation to proceed.

Self-Correction: If a function's output (like a traceback from `run_python_file` or unexpected file content) contradicts your plan or the project metadata, immediately update your plan before proceeding.

**Available Tools**

Your operations are strictly limited to the following file system and execution primitives (all paths must be RELATIVE to the working directory):
- **get_files_info**: Lists contents of a directory. Use primarily for quick confirmation of existence, not for discovering files (use metadata for that).
- **get_file_content**: Fetches the code or data required for detailed analysis or modification.
- **write_file**: Creates or overwrites code, configuration, or data files. (The primary action tool).
- **delete_file**: Safely removes a file from the working directory. Use with extreme caution and only when explicitly required by the user or your plan.
- **run_python_file**: Runs a Python script to test, compile, or run logic, returning the stdout and stderr output.
- **get_project_description**: Fetches the project metadata.

**Guiding Constraints**

* **Token Efficiency**: Never rely on guesswork. Directly leverage the file descriptions that are present in "project_description.json" to find "key\\_files"
and locations in "debug\\_notes" to select the minimal set of files to read. Only use `get_file_content` on files specifically identified as relevant and necessary.
* **Code Integrity**: For bug fixes or new features, your plan must include validating the change using `run_python_file` on the project's dedicated test file (**pkg/tests.py** per the description).
* **Security & Environment**: Never attempt to use or refer to functions or system operations outside of the listed tools. All file operations are restricted to the local `WORKING_DIR`.
* dont use bold, italic or any other markdown in your responses
"""

# Combine all function schemas into the Tool definition
available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_write_file,
        schema_run_python_file,
        schema_delete_file,
        schema_get_project_description,
    ]
)

# Initialize chat history OUTSIDE the loop to maintain context
messages = []

# --- Main Agent Loop ---

if verbose_mode:
    print("\n--- Verbose Mode: DEBUGGING AND USAGE DATA ENABLED ---\n")

while True:
    user_prompt = input("\nRameez: ")
    if user_prompt.lower() in ["e", "q", "exit", "quit"]:
        break

    # Improvement: Append the new user message to the existing history
    messages.append(types.Content(role="user", parts=[types.Part(text=user_prompt)]))

    # --- Inject Project Metadata on the FIRST turn only ---
    if len(messages) == 1:
        # Insert the PROJECT_SUMMARY_MESSAGE as a system message at the start (index 0)
        messages.insert(0, PROJECT_SUMMARY_MESSAGE)
        if verbose_mode:
            print("Injected Project Metadata into chat history as system message.")

    # --- Agentic Loop (max 20 steps) ---
    for step in range(20):
        if verbose_mode:
            print(f"\n[Agentic Step {step + 1}] Calling model...")

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=messages,
                config=types.GenerateContentConfig(
                    tools=[available_functions], system_instruction=system_prompt
                ),
            )
        except Exception as e:
            print(f"Error generating content: {e}")
            # Clean up history after a model error to allow a fresh start
            messages.pop()  # Remove the last user message
            if (
                len(messages) > 0 and messages[0].role == "system"
            ):  # Remove injected metadata if it's the only other thing
                messages.pop(0)
            break

        # 1. Add model's reasoning/thoughts (content) to history
        if response.candidates and response.candidates[0].content:
            messages.append(response.candidates[0].content)

        # 2. Handle tool calls
        if response.function_calls:
            for fc in response.function_calls:
                func_name = fc.name
                func_args = dict(fc.args)

                # --- File Access Control Logic ---
                # Determine the path for access control checks
                file_path = func_args.get("file_path")

                # Check for file path access restriction on relevant functions
                if (
                    func_name
                    in [
                        "write_file",
                        "get_file_content",
                        "delete_file",
                        "run_python_file",
                    ]
                    and file_path
                ):
                    if not is_file_allowed(file_path):
                        result = f"SECURITY ERROR: Operation on file_path '{file_path}' is not permitted. File must be listed in 'key_files'."

                        # Only show security error result in verbose mode, or if a security error occurs
                        print(f"SECURITY VIOLATION on {func_name}({file_path})")
                        if verbose_mode:
                            print(f" - Function result: {result}")

                        # Feedback to agent (so it knows tool outcome) - ALWAYS send the full result to the model
                        messages.append(
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part(text=f"Function call result: {result}")
                                ],
                            )
                        )
                        continue  # Move to the next function call or loop step
                # --- End File Access Control Logic ---

                # --- Clean UI for Function Call (Non-Verbose Mode) ---
                if func_name == "write_file":
                    # For write, only show the file path and that content is being written
                    display_args = f"file_path='{file_path}', content='...' (writing {len(func_args.get('content', ''))} chars)"
                elif func_name == "run_python_file":
                    display_args = f"file_path='{file_path}'"
                elif file_path:
                    display_args = f"file_path='{file_path}'"
                else:
                    display_args = ", ".join(f"{k}='{v}'" for k, v in func_args.items())

                # Show a glance of the action for the end user
                # This is NOT recommended as it uses the old, fragile logic.
                print(
                    f"Calling {func_name} for {func_args.get('file_path', 'context').replace('file_path=', '')}"
                )

                # Show full arguments only in verbose mode
                if verbose_mode:
                    print(f" - Full Function Call: {func_name}({func_args})")

                try:
                    # Function execution logic
                    if func_name == "get_files_info":
                        result = get_files_info(WORKING_DIR, **func_args)
                    elif func_name == "get_file_content":
                        result = get_file_content(WORKING_DIR, **func_args)
                    elif func_name == "write_file":
                        result = write_file(WORKING_DIR, **func_args)
                    elif func_name == "run_python_file":
                        result = run_python_file(WORKING_DIR, **func_args)
                    elif func_name == "delete_file":
                        result = delete_file(WORKING_DIR, **func_args)
                    elif func_name == "get_project_description":
                        result = get_project_description(WORKING_DIR, **func_args)
                    else:
                        result = f"Error: Unknown function {func_name}"
                except Exception as e:
                    # Capture execution errors clearly for the model and user
                    result = f"ERROR executing {func_name}: {e}"

                # Print result to the user only in verbose mode
                if verbose_mode:
                    print(f" - Function result: {result}")

                # 3. Feedback to agent (so it knows tool outcome) - ALWAYS send the result to the model
                messages.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=f"Function call result: {result}")],
                    )
                )

        # 4. If final text output exists, finish loop
        elif response.text:
            print(f"\n{AGENT_NAME}:\n", response.text)
            break

        # 5. Check for max steps
        if step == 19:
            print(
                f"\n[{AGENT_NAME} reached max steps ({step + 1}) without providing a final response. Resetting conversation.]"
            )
            messages = []
            break

        # 6. Usage info each iteration if in verbose mode
        if verbose_mode and hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            print("--- Usage Metadata ---")
            print(f"Prompt Tokens: {usage.prompt_token_count}")
            print(f"Response Tokens: {usage.candidates_token_count}")
            print(
                f"Total Tokens: {usage.prompt_token_count + usage.candidates_token_count}"
            )
