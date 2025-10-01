# CodeCrafter

**Status:** Fully working local agent (function-calling, read/write/execute in a scoped working directory)

**Model Used:** Gemini 2.5 Flash (via `google-genai` SDK)

**Author:** Muhammad Rameez (`Rameez`) — [rameezalipacific@gmail.com](mailto:rameezalipacific@gmail.com)
If this repo helped you, give it a star. \<3

---

## Table of contents

1.  What this is
2.  High-level design & features
3.  Safety (read this first)
4.  Prerequisites & Installation
5.  Quick setup (copy/paste)
6.  Project layout (what each file does)
7.  How to run the CLI agent (examples)
8.  Tools & Function-Calling (technical notes)
9.  Tests — what to create & run
10. Troubleshooting — common errors & fixes
11. Tips to extend (next steps / improvements)
12. Contributing, license, contact

---

## 1\. What this is (short)

A local CLI "AI coding agent" built around **Google Gemini 2.5 Flash** (using the `google-genai` SDK) that can run iterative problem-solving loops.

The agent's capabilities include:

- Listing files in a sandboxed `WORKING_DIR`.
- Reading file metadata and content (with truncation).
- Writing/overwriting files (with mandatory path safety checks).
- Executing Python files inside the working directory (with a $\mathbf{30s}$ timeout).
- Calling those functions $\mathbf{via}$ **LLM-driven function-calling** to run iterative agent loops (tool $\rightarrow$ observe $\rightarrow$ tool $\rightarrow$ observe $\rightarrow$ final answer).

You can ask the agent to inspect code, run tests, fix bugs, and (carefully) run Python scripts. This is for learning and **rapid prototyping** — **not** production use.

---

## 2\. High-level design & features

The agent follows the standard **Observe-Act** pattern, allowing the Gemini model to select and execute tools to achieve a goal.

### Core Tools

All tools are implemented as plain Python functions returning text (string or list-of-dicts). Each function has a schema for LLM function-calling:

- `get_files_info(working_directory, directory=".", verbose=True)`: Lists file metadata (path, size_kb, modified).
- `get_file_content(working_directory, file_path)`: Returns file content, truncated at `MAX_FILE_CHARS`.
- `write_file(working_directory, file_path, content)`: Writes/creates a file and returns a success/error string.
- `run_python_file(working_directory, path, args=[])`: Executes a Python file, captures $\mathbf{stdout}$ and $\mathbf{stderr}$, and enforces a $\mathbf{30s}$ timeout.

### Agentic Loop

The agent maintains a conversation history (`messages`) and runs a loop with a $\mathbf{20}$ iteration limit:

1.  The agent calls `client.models.generate_content(...)` with the full message history.
2.  **Tool Call:** If the model's response requests one or more function calls, the agent executes the function(s) locally.
3.  **Observation:** The result of the local function execution is appended to the messages as a **tool feedback message** with `role="user"`.
4.  The loop repeats, and the model attempts to generate new content or call another tool based on the new observation.
5.  **Completion:** The loop stops when the LLM returns a final `.text` response or the iteration limit is reached.

### CLI Flags

- `--verbose`: Prints per-step debug messages (LLM calls, tool inputs, and raw outputs).
- `--usage`: Prints token usage from `response.usage_metadata` (if supported by the model/SDK).

---

## 3\. Safety (read this now)

This agent has the ability to **execute arbitrary Python code** inside the `WORKING_DIR`. This power is highly convenient for a coding agent but $\mathbf{extremely}$ $\mathbf{dangerous}$ if not controlled.

- **Never** run this on untrusted code or share the environment with others.
- The code **enforces directory boundaries** by validating that the absolute path of any file operation starts with the `WORKING_DIR` path. **Do not modify this check** unless you fully understand the security implications.
- Execution has a $\mathbf{30s}$ timeout to prevent runaway processes.
- $\mathbf{Always}$ keep the working directory restricted to a controlled project folder.

If you are not comfortable with code execution, you must **disable** the `run_python_file` function and remove its declaration from the function registration list in $\mathbf{main.py}$. ;)

---

## 4\. Prerequisites & Installation

### Requirements

- **Python $\mathbf{3.10+}$** (The project was developed and tested using Python 3.11).
- **Google Gemini API key (`GEMINI_API_KEY`)**: The [Gemini API free tier](https://ai.google.dev/pricing) is suitable for testing, but monitor request limits for higher-volume usage.
- Required Python packages: `google-genai` and `python-dotenv`.

### Installation Steps

Use a virtual environment (`venv`) to manage dependencies.

```bash
# 1. Create venv
python -m venv .venv
# 2. Activate venv (use the correct command for your shell)
#    - mac/linux: source .venv/bin/activate
#    - Windows (cmd.exe): .venv\Scripts\activate.bat
# 3. Upgrade pip and install packages
pip install --upgrade pip
pip install google-genai python-dotenv
```

---

## 5\. Quick setup (copy/paste)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd <your-repo-dir>

# 2. Activate venv (see Step 2 in Section 4)
source .venv/bin/activate

# 3. Create .env file with your API key
echo GEMINI_API_KEY=sk-... > .env

# 4. Check/Confirm WORKING_DIR variable in main.py
#    It should point to your target project folder (e.g., 'calculator/')

# 5. Run the agent
python main.py
```

---

## 6\. Project layout (what to look for)

This layout separates the core agent logic (`main.py`) from the reusable tool definitions (`functions/`).

```
.
├─ main.py                     # CLI entry, agentic loop, tool registration, and system prompt.
├─ .env                        # GEMINI_API_KEY (must NOT be committed to git)
├─ functions/
│  ├─ get_files_info.py        # Tool definition + types.FunctionDeclaration schema
│  ├─ get_file_content.py      # Tool definition + types.FunctionDeclaration schema
│  ├─ write_file.py            # Tool definition + types.FunctionDeclaration schema
│  └─ run_python_file.py       # Tool definition + types.FunctionDeclaration schema
├─ calculator/                 # The WORKING_DIR (example project for testing)
│  ├─ main.py                 # Example executable file
│  └─ pkg/                    # Example package
└─ README.md
```

**Note on Imports:** Function files $\mathbf{must}$ **not** run test code on import. Ensure all tests are wrapped with a name guard:

```python
if __name__ == "__main__":
    # Test code here
```

---

## 7\. How to run the CLI agent — examples

### Basic Interaction

```bash
python main.py
# Agent will wait for input. Ask:
Rameez: how does the calculator render results to the console?
```

### Debugging & Usage Tracking

```bash
python main.py --verbose --usage
```

### Sample Conversation Output (Condensed)

The agent will show its thought process by displaying function calls:

```
Rameez: how does the calculator render results to the console?
 - Calling function: get_files_info({'directory': '.'})
Found: main.py | Size: 0.74 KB | Modified: 2025-09-28 12:50:45
...
 - Calling function: get_file_content({'file_path': 'main.py'})
# main.py content...
Final response:
 The calculator prints the formatted JSON returned from format_json_output(...)
```

### Example Test Prompt

To test its write and execute capabilities:

```
Rameez: fix the bug: 3 + 7 * 2 shouldn't be 20. Make it follow order of operations.
# Agent may call write_file, run_python_file etc, then respond with final result.
```

---

## 8\. Tools & Function-Calling (technical notes)

Function-calling is achieved by passing a list of `types.FunctionDeclaration` objects to the model's configuration.

### Schema Validation Rules

- **Parameter Names Must Match:** Schema parameter names must $\mathbf{exactly}$ match your Python function’s parameter names. If the schema uses `path` but the function uses `file_path`, the call will fail with a `TypeError`.
- **Array $\mathbf{items}$:** If you define an array parameter (e.g., `args` for CLI arguments), you $\mathbf{must}$ declare the `items` type (e.g., `items=types.Schema(type=types.Type.STRING)`). Failing to do so results in a $\mathbf{400}$ $\mathbf{INVALID\_ARGUMENT}$ error.

### Tool Result Role

When the result of a local tool execution is appended back to the message history, it must use the $\mathbf{correct}$ $\mathbf{role}$ to prevent a $\mathbf{400}$ $\mathbf{INVALID\_ARGUMENT}$ error:

```python
# Append tool result as a new observation message
messages.append(
    types.Content(role="user", parts=[types.Part(text=str(tool_result))])
)
```

### $\mathbf{generate\_content}$ Configuration

The tools are registered in the request configuration:

```python
response = client.models.generate_content(
    model="gemini-2.5-flash", # Specific model
    contents=messages,
    config=types.GenerateContentConfig(
        tools=[available_functions],
        system_instruction=system_prompt # Guiding the model's behavior
    )
)
```

---

## 9\. Tests — what to create & run

A robust agent needs comprehensive testing of its tools and safety mechanisms.

### File Setup

1.  **Large File Test (`lorem.txt`):** Create a file with over $\mathbf{10,000}$ characters inside the `calculator/` directory to test the content **truncation** logic in `get_file_content`.
2.  **Isolated Tests:** Ensure tests inside $\mathbf{functions/*}$ are guarded with `if __name__ == "__main__":` so they are not accidentally executed during import.

### Manual Test Cases (Tool Level)

- **Truncation:** Run `get_file_content("calculator", "lorem.txt")` and confirm it returns truncated content with the $\mathbf{...}$ $\mathbf{truncated}$ $\mathbf{at}$ marker.
- **Write/Read Cycle:** Use `write_file` to create a new file, then use `get_file_content` to verify its content.
- **Execution:** Run `run_python_file("calculator", "main.py")` with and without arguments to test $\mathbf{stdout}$ and argument passing.
- **Directory Boundary Safety (Critical):**
  - Test `get_file_content("calculator", "/bin/cat")` $\rightarrow$ should return an $\mathbf{error}$ (outside working directory).
  - Test `run_python_file("calculator", "../main.py")` $\rightarrow$ should return an $\mathbf{error}$ (outside working directory).

### Agent Test Prompts (End-to-End)

Run the CLI and ask the agent to perform multi-step tasks:

- **Inspection:** "Explain the role of `render.py`." (Tests `get_files_info` $\rightarrow$ `get_file_content` $\rightarrow$ final answer).
- **Debugging:** "Run `main.py` with arguments 5, plus, 3, times, 2. It should result in 13. Fix it if it doesn't." (Tests `run_python_file` $\rightarrow$ `write_file` $\rightarrow$ `run_python_file` $\rightarrow$ final answer).

---

## 10\. Troubleshooting — common errors & fixes

### `ModuleNotFoundError: No module named 'google.genai'`

- **Cause:** The package is not installed in the active virtual environment.
- **Fix:** Activate your venv and run `pip install google-genai`.

### `TypeError: Models.generate_content() got an unexpected keyword argument 'tools'`

- **Cause:** An older version of the `google-genai` SDK is in use, which lacks the modern function-calling support.
- **Fix:** Upgrade the package: `pip install --upgrade google-genai`.

### `400 INVALID_ARGUMENT. Please use a valid role: user, model.`

- **Cause:** Appending a tool result or non-standard message to the history with an invalid `role` (e.g., `role="function"` or `role="tool"`).
- **Fix:** Tool results must be appended as $\mathbf{role="user"}$ (see Section 8).

### `400 INVALID_ARGUMENT ... items: missing field` for $\mathbf{args}$ array

- **Cause:** The schema for an array parameter lacks the required $\mathbf{items}$ type declaration.
- **Fix:** Ensure the schema declares the type of elements in the array (e.g., `items=types.Schema(type=types.Type.STRING)`).

### $\mathbf{run\_python\_file()}$ $\mathbf{got}$ $\mathbf{an}$ $\mathbf{unexpected}$ $\mathbf{keyword}$ $\mathbf{argument}$ $\mathbf{'path'}$.

- **Cause:** The parameter name in the $\mathbf{FunctionDeclaration}$ schema (e.g., `path`) does not match the argument name in the Python function signature (e.g., `file_path`).
- **Fix:** Make the schema parameter name and the Python function argument name match $\mathbf{exactly}$.

### Tests or prints showing up on startup

- **Cause:** Test blocks or print statements are executed at module import time.
- **Fix:** Wrap all such code in the `if __name__ == "__main__":` guard.

### Path problems on Windows

- If your `WORKING_DIR` is a relative string (e.g., `"calculator"`), it is safer to use absolute paths.

- **Fix:** Auto-detect the absolute path in $\mathbf{main.py}$ using the $\mathbf{os}$ module:

  ```python
  import os
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
  WORKING_DIR = os.path.join(BASE_DIR, "calculator")
  ```

---

## 11\. Tips to extend (next steps / improvements)

- **Auto-Debug/Repair Loop:** Implement a more advanced loop where the agent is specifically prompted to $\mathbf{read}$ $\mathbf{failing}$ $\mathbf{tracebacks}$ from `run_python_file`, $\mathbf{write}$ $\mathbf{corrections}$ via `write_file`, and $\mathbf{re-run}$ the test until it passes (while respecting the iteration limit).
- **Memory Persistence:** Integrate a persistent memory store (e.g., a simple JSON file or an embedding-based RAG system) to allow the agent to recall previous conversations or knowledge about the project between runs.
- **Secure Sandboxing:** For enterprise use, investigate using technologies like $\mathbf{Docker}$ $\mathbf{containers}$ or $\mathbf{separate}$ $\mathbf{low-privilege}$ $\mathbf{users}$ to execute Python files, which can completely disallow network access or access to other system files.
- **Permission Model:** Introduce an $\mathbf{interactive}$ step for destructive actions like `write_file` and `run_python_file` when in a high-risk environment.
- **True Unit Tests:** Formalize the testing process by adding $\mathbf{pytest}$ or $\mathbf{unittest}$ cases to assert the correctness of tool outputs and the integrity of safety checks, rather than relying on manual checks.

---

## 12\. Contributing, license & contact

- If you find this repository useful: $\mathbf{star}$ $\mathbf{it}$. Stars help maintainers continue to build and share useful tools. ;)
- **License:** MIT. (It is recommended to create a `LICENSE` file for open-source clarity).
- **Author / Contact:** **Muhammad Rameez** — [rameezalipacific@gmail.com](mailto:rameezalipacific@gmail.com)
  If you fork or modify this agent, I'd appreciate a short message—I enjoy seeing how others leverage this work.

---
