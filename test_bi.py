from backend.main import understand_question

print("Testing Sales BI Gemini function...")

try:
    result = understand_question("What is the total revenue?")
    print("SUCCESS!")
    print("Generated query plan:")
    print(result)

except Exception as e:
    print("FAILED:", repr(e))