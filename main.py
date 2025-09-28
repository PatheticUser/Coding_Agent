import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Parse CLI flags
args = sys.argv[1:]
verbose_mode = "--verbose" in args
usage_mode = "--usage" in args

# Initialize chat history
messages = []

if verbose_mode:
    print("[Verbose Mode Enabled]")
if usage_mode:
    print("[Usage Tracking Enabled]")

while True:
    user_prompt = input("\nYou: ")
    if user_prompt.lower() in ["exit", "quit"]:
        print("Ending chat.")
        break

    # Append user message
    messages.append(types.Content(role="user", parts=[types.Part(text=user_prompt)]))

    # Verbose logs
    if verbose_mode:
        print("[Sending Messages to API...]")
        print(f"[Message Count: {len(messages)}]")

    # Generate response with context
    response = client.models.generate_content(
        model="gemini-2.0-flash-001", contents=messages
    )

    reply = response.text
    print(f"Gemini: {reply}")

    # Append model reply to history
    messages.append(types.Content(role="model", parts=[types.Part(text=reply)]))

    # Optional usage info
    if usage_mode:
        usage = response.usage_metadata
        print("\n--- Usage Metadata ---")
        print(f"Prompt Tokens: {usage.prompt_token_count}")
        print(f"Response Tokens: {usage.candidates_token_count}")
        print(
            f"Total Tokens: {usage.prompt_token_count + usage.candidates_token_count}"
        )
