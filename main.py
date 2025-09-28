import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Initialize chat history
messages = []

while True:
    user_prompt = input("\nYou: ")
    if user_prompt.lower() in ["exit", "quit"]:
        print("Ending chat.")
        break

    # Append user message
    messages.append(types.Content(role="user", parts=[types.Part(text=user_prompt)]))

    # Generate response with full history
    response = client.models.generate_content(
        model="gemini-2.0-flash-001", contents=messages
    )

    # Extract response text
    reply = response.text
    print(f"Gemini: {reply}")

    # Append model's response to history
    messages.append(types.Content(role="model", parts=[types.Part(text=reply)]))

    # Show usage stats
    usage = response.usage_metadata
    print("\n--- Usage Metadata ---")
    print(f"Prompt Tokens: {usage.prompt_token_count}")
    print(f"Response Tokens: {usage.candidates_token_count}")
