import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Take prompt from user
prompt = input("Enter your prompt: ")

response = client.models.generate_content(model="gemini-2.0-flash-001", contents=prompt)

# Print the generated text
print("\nResponse:\n", response.text)

# Print token usage metadata
usage = response.usage_metadata
print("\n--- Usage Metadata ---")
print(f"Prompt Tokens: {usage.prompt_token_count}")
print(f"Response Tokens: {usage.candidates_token_count}")
