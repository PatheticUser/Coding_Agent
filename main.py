import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.get_files_info import get_files_info, schema_get_files_info

# --- Load environment variables ---
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# --- Parse CLI flags ---
args = sys.argv[1:]
verbose_mode = "--verbose" in args
usage_mode = "--usage" in args

# --- Initialize chat history ---
messages = []

if verbose_mode:
    print("Verbose mode enabled")
if usage_mode:
    print("Usage tracking enabled")

# --- Register tools (function calling support) ---
tools = [types.Tool(function_declarations=[schema_get_files_info])]

# --- Working directory setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = os.path.join(BASE_DIR, "calculator")
SUB_DIR = "pkg"


# --- Chat loop ---
while True:
    user_prompt = input("\nYou: ")
    if user_prompt.lower() in ["exit", "quit"]:
        print("Ending chat.")
        break

    # Append user message
    messages.append(types.Content(role="user", parts=[types.Part(text=user_prompt)]))

    if verbose_mode:
        print(f"Message count: {len(messages)}")

    # Generate response with context + tools
    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=messages,
        tools=tools,
    )

    # --- Check if function call is suggested ---
    if response.candidates and response.candidates[0].content.parts:
        part = response.candidates[0].content.parts[0]
        if part.function_call and part.function_call.name == "get_files_info":
            print("\n[Gemini requested to call get_files_info]")

            # Call the actual function with working_directory + directory
            result = get_files_info(WORKING_DIR, SUB_DIR, verbose=verbose_mode)

            # Append function result
            messages.append(
                types.Content(
                    role="function",
                    parts=[
                        types.Part(
                            function_response=types.FunctionResponse(
                                name="get_files_info",
                                response={"result": result},
                            )
                        )
                    ],
                )
            )

            # Re-run model with function result
            response = client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=messages,
            )

    # --- Extract reply ---
    reply = response.text
    print(f"Gemini: {reply}")

    # Append model reply
    messages.append(types.Content(role="model", parts=[types.Part(text=reply)]))

    # --- Optional usage info ---
    if usage_mode:
        usage = response.usage_metadata
        print("\n--- Usage Metadata ---")
        print(f"Prompt Tokens: {usage.prompt_token_count}")
        print(f"Response Tokens: {usage.candidates_token_count}")
        print(
            f"Total Tokens: {usage.prompt_token_count + usage.candidates_token_count}"
        )
