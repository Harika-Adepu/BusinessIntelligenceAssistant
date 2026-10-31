import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

print("Testing Gemini connection...")

try:
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="What is 2 + 2?"
    )

    print("SUCCESS!")
    print(response.text)

except Exception as e:
    import traceback
    print("FAILED:", repr(e))
    traceback.print_exc()