import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=20000,
    thinking={"type": "enabled", "budget_tokens": 16000},
    messages=[
        {
            "role": "user",
            "content": "Hello Claude! Can you tell me a bit about yourself?",
        }
    ],
)

# Process the response content
for content_block in response.content:
    if content_block.type == "thinking":
        thinking_content = content_block.thinking
    elif content_block.type == "text":
        text_content = content_block.text


# Print the results
print("=" * 50)
print("THINKING:")
print("=" * 50)
print(thinking_content if thinking_content else "No thinking content found")
print("\n" + "=" * 50)
print("RESPONSE TEXT:")
print("=" * 50)
print(text_content if text_content else "No text content found")
