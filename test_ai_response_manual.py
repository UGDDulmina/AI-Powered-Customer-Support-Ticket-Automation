from app.services.ai_response_service import generate_test_response

result = generate_test_response()

print("AI Generated Response:")
print(result)

assert isinstance(result, str)
assert result.strip()