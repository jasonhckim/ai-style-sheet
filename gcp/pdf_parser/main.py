from shared import auth, drive_utils
import fitz
import functions_framework
import base64
import json

@functions_framework.http
def main(request):
    data = request.get_json()
    file_id = data.get("file_id")
    file_name = data.get("file_name")
    folder_id = data.get("folder_id")

    if not file_id or not file_name:
        return "Missing file_id or file_name", 400

    pdf_path = drive_utils.download_file_from_drive(file_id, file_name)
    extracted = drive_utils.extract_text_and_images_from_pdf(pdf_path)

    # Publish each page of data to Pub/Sub
    from google.cloud import pubsub_v1
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(auth.GCP_PROJECT, "pdf-processed")

    for item in extracted:
        message = {
            "style_number": item["style_number"],
            "text": item["text"],
            "images": item["images"],
            "file_name": file_name,
            "folder_id": folder_id,
        }
        publisher.publish(topic_path, json.dumps(message).encode("utf-8"))

    return "✅ PDF parsed and pushed to Pub/Sub", 200

