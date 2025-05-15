import os
import json
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import secretmanager

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def access_secret(secret_id):
    """Fetch secret from Secret Manager (used in GCP runtime)."""
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("GCP_PROJECT")
    secret_path = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": secret_path})
    return response.payload.data.decode("utf-8")

def get_creds():
    """Get service account credentials either from env var or Secret Manager."""
    if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
        info = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    else:
        # Runtime in GCP, use Secret Manager
        raw_json = access_secret("GOOGLE_APPLICATION_CREDENTIALS")
        info = json.loads(raw_json)

    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

def get_gspread_client():
    return gspread.authorize(get_creds())

def get_drive_service():
    return build("drive", "v3", credentials=get_creds())
