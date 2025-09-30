import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import your function implementations and schemas
from functions.get_files_info import get_files_info, schema_get_files_info
from functions.get_file_content import get_file_content, schema_get_file_content
from functions.write_file import write_file, schema_write_file
from functions.run_python_file import run_python_file, schema_run_python_file

# Load environment variables
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Parse CLI flags
args = sys.argv[1:]
verbose_mode = "--verbose" in args
usage_mode = "--usage" in args

# Hardcoded working directory
WORKING_DIR = r"C:\Users\Ash\Downloads\Coding Agent\Coding_Agent\calculator"

# System prompt
system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read a file's contents
- Write or overwrite a file
- Execute a Python file

All paths you provide should be relative to the working directory.
You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""

# Combine all function schemas
available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_write_file,
        schema_run_python_file,
    ]
)

# Initialize chat history
messages = []

if verbose_mode:
    print("[Verbose Mode Enabled]")
if usage_mode:
    print("[Usage Tracking Enabled]")

while True:
    user_prompt = input("Rameez: ")
    if user_prompt.lower() in ["exit", "quit"]:
        print("Ending chat.")
        break

    # reset message history for each new user prompt
    messages = [types.Content(role="user", parts=[types.Part(text=user_prompt)])]

    if verbose_mode:
        print("[Verbose Mode Enabled]")
        print("[Sending initial message to API...]")

    # --- Agentic Loop (max 20 steps) ---
    for step in range(20):
        if verbose_mode:
            print(f"\n[Agentic Step {step + 1}] Calling model...")

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=messages,
                config=types.GenerateContentConfig(
                    tools=[available_functions], system_instruction=system_prompt
                ),
            )
        except Exception as e:
            print(f"Error generating content: {e}")
            break

        # Add candidate responses (like reasoning / thoughts)
        for cand in response.candidates:
            if cand.content:
                messages.append(cand.content)

        # Handle tool calls
        if response.function_calls:
            for fc in response.function_calls:
                print(f" - Calling function: {fc.name}({fc.args})")

                try:
                    if fc.name == "get_files_info":
                        result = get_files_info(WORKING_DIR, **fc.args)
                    elif fc.name == "get_file_content":
                        result = get_file_content(WORKING_DIR, **fc.args)
                    elif fc.name == "write_file":
                        result = write_file(WORKING_DIR, **fc.args)
                    elif fc.name == "run_python_file":
                        result = run_python_file(WORKING_DIR, **fc.args)
                    else:
                        result = f"Error: Unknown function {fc.name}"
                except Exception as e:
                    result = f"Error executing {fc.name}: {e}"

                # Print result + feedback
                print(result)

                # Feedback to agent (so it knows tool outcome)
                messages.append(
                    types.Content(role="user", parts=[types.Part(text=str(result))])
                )

        # If final text output exists, finish loop
        elif response.text:
            print("\nFinal response:\n", response.text)
            messages.append(
                types.Content(role="model", parts=[types.Part(text=response.text)])
            )
            break

        # usage info each iteration if requested
        if usage_mode and hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            print("\n--- Usage Metadata ---")
            print(f"Prompt Tokens: {usage.prompt_token_count}")
            print(f"Response Tokens: {usage.candidates_token_count}")
            print(
                f"Total Tokens: {usage.prompt_token_count + usage.candidates_token_count}"
            )
    else:
        print("\n[Agent reached max steps without final output]")
