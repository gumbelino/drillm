# This example is the new way to use the OpenAI lib for python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["LLAMA_API_KEY"], base_url="https://api.llama-api.com"
)

response = client.chat.completions.create(
    model="llama3.1-70b",
    messages=[
        {"role": "user", "content": "Who were the founders of Microsoft?"},
    ],
)

# print(response)
print(response.model_dump_json(indent=2))
print(response.choices[0].message.content)
