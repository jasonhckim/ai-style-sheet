from flask import Flask, request
from shared import common
import os
import openai
import json
from google.cloud import pubsub_v1

app = Flask(__name__)
openai.api_key = os.environ["OPENAI_API_KEY"]

@app.route("/", methods=["POST"])
def main():
    envelope = request.get_json()
    data = json.loads(base64.b64decode(envelope["message"]["data"]).decode("utf-8"))

    prompt = common.build_prompt(data["style_number"], data["text"], data["images"][0]["image_url"])
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    result = common.parse_completion(response)
    data.update(result)

    # Send to next topic
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(common.GCP_PROJECT, "descriptions-generated")
    publisher.publish(topic_path, json.dumps(data).encode("utf-8"))

    return "✅ Description generated", 200
