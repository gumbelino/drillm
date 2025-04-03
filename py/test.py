import anthropic

client = anthropic.Anthropic()

models = client.models.list()

for model in models:
    print(model.id)
