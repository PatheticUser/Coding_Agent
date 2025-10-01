import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- IMPORTANT: Assume your function implementations and schemas are defined in 'functions' directory ---
# NOTE: The actual content of these files is assumed to be correct based on your setup.
from functions.get_files_info import get_files_info, schema_get_files_info
from functions.get_file_content import get_file_content, schema_get_file_content
from functions.write_file import write_file, schema_write_file
from functions.run_python_file import run_python_file, schema_run_python_file

# --- Configuration & Initialization ---

# Load environment variables
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

try:
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not found.")
    client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    sys.exit(1)

# Parse CLI flags
args = sys.argv[1:]
verbose_mode = "--verbose" in args
usage_mode = "--usage" in args

# Hardcoded working directory (Ensure this is correct and accessible!)
WORKING_DIR = r"C:\Users\Ash\Downloads\Coding Agent\Coding_Agent\calculator"
if verbose_mode:
    print(f"[Working Directory: {WORKING_DIR}]")

# System prompt (The instruction set for the model)
system_prompt = """
You are CodeForge, an expert developer's AI assistant operating in a closed, local coding environment. Your singular goal is to efficiently and reliably complete the user's software development and file-related requests.

Core Protocol: Plan, Act, Report
You must adhere to a strict Chain of Thought (CoT) workflow to ensure strategic execution:

1. ANALYZE & PLAN (CoT): First, analyze the user's goal. Before calling any function, you must generate a clear, step-by-step **Function Call Plan**. This plan should outline the specific sequence of operations required to achieve the ultimate goal.

2. EXECUTE: Perform the next single function call from your plan.

3. REPORT: Present the results and, if the task is complete, summarize the final outcome. If the task is ongoing, present the updated plan and ask for confirmation to proceed.

Self-Correction: If a function's output changes the required path (e.g., a file list is different than expected), immediately update the remainder of your plan before proceeding.

Available Tools
Your operations are strictly limited to the following four file system and execution primitives (all paths must be RELATIVE to the working directory):
- **get_files_info**: Lists contents of a directory. (For discovery and confirmation).
- **get_file_content**: Fetches the code or data required for analysis or modification.
- **write_file**: Creates or overwrites code, configuration, or data files. (The primary action tool).
- **run_python_file**: Runs a Python script to test, compile, or run logic, returning the stdout output.

Guiding Constraints
Holistic Thinking: Consider the full scope of the request. For code creation or modification, ensure your plan accounts for reading existing files, creating tests (if applicable), writing the solution, and finally, testing the result.
Output Focus: When you write_file, the content must be complete and correct. When you run_python_file, the returned output is your only measure of success or failure.
Security & Environment: Never attempt to use or refer to functions or system operations outside of the four listed above.
"""

# Combine all function schemas into the Tool definition
available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_write_file,
        schema_run_python_file,
    ]
)

# Initialize chat history OUTSIDE the loop to maintain context
messages = []

# --- Main Agent Loop ---

if verbose_mode:
    print("\n[Verbose Mode Enabled]")
if usage_mode:
    print("[Usage Tracking Enabled]")

print("\n--- CodeForge AI Agent Initialized ---")

while True:
    user_prompt = input("Rameez: ")
    if user_prompt.lower() in ["exit", "quit"]:
        print("Ending chat.")
        break

    # Improvement: Append the new user message to the existing history
    messages.append(types.Content(role="user", parts=[types.Part(text=user_prompt)]))

    # --- Agentic Loop (max 20 steps) ---
    for step in range(20):
        if verbose_mode:
            print(f"\n[Agentic Step {step + 1}] Calling model...")

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",  # Using a recent, capable model
                contents=messages,
                config=types.GenerateContentConfig(
                    tools=[available_functions], system_instruction=system_prompt
                ),
            )
        except Exception as e:
            print(f"Error generating content: {e}")
            # Improvement: Remove the last user message to allow retry on next loop
            messages.pop()
            break

        # 1. Add model's reasoning/thoughts (content) to history
        # This includes the plan and any final text response
        if response.candidates and response.candidates[0].content:
            # The model's *actual* content (including the plan) must have the role 'model'
            messages.append(response.candidates[0].content)

        # 2. Handle tool calls
        if response.function_calls:
            for fc in response.function_calls:
                # Get the function's name and arguments
                func_name = fc.name
                func_args = dict(fc.args)

                print(f" - Calling function: {func_name}({func_args})")

                # Extract the relative path, which is assumed to be the first argument
                # The agent is instructed to use relative paths, but the Python wrapper
                # is responsible for joining it with the WORKING_DIR for security.

                try:
                    if func_name == "get_files_info":
                        # For get_files_info, we pass the WORKING_DIR and let the function figure out the path
                        result = get_files_info(WORKING_DIR, **func_args)
                    elif func_name == "get_file_content":
                        result = get_file_content(WORKING_DIR, **func_args)
                    elif func_name == "write_file":
                        result = write_file(WORKING_DIR, **func_args)
                    elif func_name == "run_python_file":
                        result = run_python_file(WORKING_DIR, **func_args)
                    else:
                        result = f"Error: Unknown function {func_name}"
                except Exception as e:
                    # Capture execution errors clearly for the model and user
                    result = f"ERROR executing {func_name} with args {func_args}: {e}"

                # Print result to the user
                print(f" - Function result: {result}")

                # 3. Feedback to agent (so it knows tool outcome)
                # The result of a function call is treated as observation/feedback, so the role is 'user'
                messages.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=f"Function call result: {result}")],
                    )
                )

        # 4. If final text output exists, finish loop
        elif response.text:
            print("\nCodeForge:\n", response.text)
            # The model's final text response is ALREADY added to history in step 1.
            break

        # Check for max steps
        if step == 19:
            print(
                "\n[Agent reached max steps without providing a final response. Resetting conversation.]"
            )
            messages = []
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
