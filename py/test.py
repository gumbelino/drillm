import cohere

co = cohere.Client()
response = co.models.list()

for model in response.models:
    if "command" in model.name:
        print(f"\n====== {model.name} ======")
        print(f"\tContext length: {model.context_length}")
        print(f"\tFine-tunned: {model.finetuned}")
