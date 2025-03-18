# """
# Lists the available Amazon Bedrock models.
# """

import logging
import json
import boto3


from botocore.exceptions import ClientError


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# def list_foundation_models(bedrock_client):
#     """
#     Gets a list of available Amazon Bedrock foundation models.

#     :return: The list of available bedrock foundation models.
#     """

#     try:
#         response = bedrock_client.list_foundation_models()
#         models = response["modelSummaries"]
#         logger.info("Got %s foundation models.", len(models))
#         return models

#     except ClientError:
#         logger.error("Couldn't list foundation models.")
#         raise


# def main():
#     """Entry point for the example. Uses the AWS SDK for Python (Boto3)
#     to create an Amazon Bedrock client. Then lists the available Bedrock models
#     in the region set in the callers profile and credentials.
#     """

#     bedrock_client = boto3.client(service_name="bedrock")

#     fm_models = list_foundation_models(bedrock_client)
#     for model in fm_models:
#         print(f"Model: {model['modelName']}")
#         print(json.dumps(model, indent=2))
#         print("---------------------------\n")

#     logger.info("Done.")


# if __name__ == "__main__":
#     main()


# Set up the Amazon Bedrock client
bedrock_client = boto3.client(service_name="bedrock-runtime", region_name="eu-north-1")

model_id = (
    "arn:aws:bedrock:eu-north-1:872515253478:inference-profile/eu.amazon.nova-lite-v1:0"
)

prompt = "Hello, how are you?"

payload = {
    "max_tokens": 2048,
    "temperature": 0.9,
    "top_k": 250,
    "top_p": 1,
    "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
}

# Invoke the Amazon Bedrock model
response = bedrock_client.invoke_model(modelId=model_id, body=json.dumps(payload))

# Process the response
result = json.loads(response["body"].read())
generated_text = "".join([output["text"] for output in result["content"]])
print(f"Response: {generated_text}")
