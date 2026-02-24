import boto3, json, os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_DEFAULT_REGION"))

model_id = "anthropic.claude-3-haiku-20240307-v1:0"

payload = {
  "anthropic_version": "bedrock-2023-05-31",
  "max_tokens": 80,
  "messages": [{"role": "user", "content": "Reply with only: OK"}]
}

resp = client.invoke_model(
    modelId=model_id,
    body=json.dumps(payload),
    contentType="application/json",
    accept="application/json"
)

print(json.loads(resp["body"].read()))