import cohere

co = cohere.Client()
response = co.models.list()

for model in response.models:
    print(model.name)
