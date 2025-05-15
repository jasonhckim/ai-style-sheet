import os
import json
from google.oauth2 import service_account
import gspread
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_creds():
    service_account_info = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    return creds

def get_gspread_client():
    creds = get_creds()
    return gspread.authorize(creds)

def get_drive_service():
    creds = get_creds()
    return build("drive", "v3", credentials=creds)
