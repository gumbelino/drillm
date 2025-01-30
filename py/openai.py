import requests
import json
import csv

API_KEYS_FILE_PATH = "../private/api_keys.csv"


def get_chatgpt_response(prompt, api_key):
    url = "https://api.openai.com/v1/engines/davinci-codex/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {"prompt": prompt}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}


def read_api_keys_from_csv(file_path):
    api_keys = {}
    with open(file_path, mode="r") as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            provider, api_key = row
            api_keys[provider] = api_key
    return api_keys


if __name__ == "__main__":
    api_keys = read_api_keys_from_csv(API_KEYS_FILE_PATH)
    api_key = api_keys.get("openai", "your_openai_api_key_here")
    prompt = "Hello, how are you?"
    response = get_chatgpt_response(prompt, api_key)
    print(json.dumps(response, indent=4))
