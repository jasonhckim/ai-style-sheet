from modules import ai_description
from modules import google_drive
from modules import utils
import pandas as pd
import yaml
import gspread
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
import googleapiclient
# ✅ Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()  # Loads .env before any other imports

# Now import modules that depend on the environment variables
from modules import ai_description
from modules import google_drive

# ✅ Load Configuration from YAML
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# ✅ Retrieve Folder IDs from Config
PDF_FOLDER_ID = config["drive_folder_ids"]["pdf"]
DOC_FOLDER_ID = config["drive_folder_ids"]["doc"]
CSV_FOLDER_ID = config["drive_folder_ids"]["csv"]

import os, json
from google.oauth2.service_account import Credentials
import gspread

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
  
def get_keywords_from_drive():
    """Fetches keywords from the latest document in Google Drive."""
    doc_file = google_drive.list_files_in_drive(DOC_FOLDER_ID, "text/plain")
    
    if doc_file:
        doc_path = google_drive.download_file_from_drive(doc_file["id"], "keywords.txt")
        return utils.extract_keywords_from_doc(doc_path) if doc_path else []
    
    return []




def upload_to_google_sheets(df, pdf_filename, pdf_folder_id):
    """Uploads the DataFrame to a Google Sheet named after the PDF file and ensures it is moved to the correct Google Drive folder."""

    # ✅ Extract the base name of the PDF file (without extension)
    sheet_name = pdf_filename.replace(".pdf", "")

    # ✅ Authenticate with Google Sheets API
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    service_account_json = os.environ["GOOGLE_CREDENTIALS"]  # must exist
    info = json.loads(service_account_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    drive_service = build("drive", "v3", credentials=creds)
        client = gspread.authorize(creds)
        print("DEBUG: client is defined:", client)

    # ✅ Try to open existing Google Sheet, otherwise create it
    try:
        client = gspread.authorize(creds)
        print("DEBUG: client is defined:", client)
        sheet = client.open(sheet_name)
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"🛑 Google Sheet '{sheet_name}' not found. Creating a new one...")

        # ✅ Create a new Google Sheet
        sheet = client.create(sheet_name)

    drive_service = build("drive", "v3", credentials=creds)  # Ensure proper API usage
    file_id = sheet.id  # Get the newly created sheet's ID

    # ✅ List all sheets to confirm it's created
    file_list = drive_service.files().list(q=f"name='{sheet_name}'", fields="files(id, name, parents)").execute()
    if file_list["files"]:
        file_id = file_list["files"][0]["id"]  # Get the correct file ID
        print(f"✅ Found Google Sheet: {sheet_name} (ID: {file_id})")

        try:
            drive_service.files().update(
                fileId=file_id,
                addParents=pdf_folder_id,  # Move to the correct folder
                removeParents="root",  # Remove from default My Drive location
                fields="id, parents"
            ).execute()
            print(f"✅ Google Sheet '{sheet_name}' moved to folder: {pdf_folder_id}")
        except Exception as e:
            print(f"❌ ERROR: Failed to move Google Sheet '{sheet_name}' to folder: {pdf_folder_id}. Debug: {e}")
    else:
        print(f"❌ ERROR: Could not find Google Sheet '{sheet_name}' in Drive.")

    # ✅ Select the first worksheet (or create it)
    worksheet = sheet.get_worksheet(0) or sheet.add_worksheet(title="Sheet1", rows="1000", cols="10")

    # ✅ Convert DataFrame to list of lists for Google Sheets
    data = [df.columns.tolist()] + df.values.tolist()

    # ✅ Clear and update the sheet
    worksheet.clear()
    worksheet.update(values=data, range_name="A1")

    print(f"✅ Data successfully uploaded to Google Sheet: {sheet.url}")



def process_pdf():
    """Extracts data from the latest PDF, generates descriptions, and uploads both files to Google Sheets."""
    # Initialize variables first
    extracted_data = []
    processed_data = []
    
    pdf_file = google_drive.list_files_in_drive(PDF_FOLDER_ID, "application/pdf")

    if pdf_file:
        pdf_filename = pdf_file["name"]  # Get the actual name of the PDF
        pdf_path = google_drive.download_file_from_drive(pdf_file["id"], pdf_filename)
        
        if pdf_path:  # Check if download succeeded
            extracted_data = google_drive.extract_text_and_images_from_pdf(pdf_path)
        else:
            print("❌ Failed to download PDF file")
            return

        # ✅ Fetch Keywords from Drive
        keywords = get_keywords_from_drive()

        # ✅ Generate descriptions (AFTER extracted_data is populated)
        processed_data = [
            ai_description.generate_description(entry["style_number"], entry["images"], keywords) 
            for entry in extracted_data
        ]

        # ✅ Debug: Print the structure of the first item
        if processed_data:
            print("Sample processed entry:", processed_data[0])

        # ✅ Convert to DataFrame
        df = pd.DataFrame(processed_data)

        # ✅ Ensure proper column order
        expected_columns = [
            "Style Number", "Product Title", "Product Description", "Tags", 
            "Product Category", "Product Type", "Option2 Value", "Keywords"
        ]
        
        # Add column validation
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ Missing columns in DataFrame: {missing_columns}")
            return

        df = df[expected_columns]

        # ✅ Upload the data to a Google Sheet
        upload_to_google_sheets(df, pdf_filename, PDF_FOLDER_ID)
        print(f"✅ Process completed. Files in folder: {PDF_FOLDER_ID}")
    else:
        print("❌ No PDF found in Google Drive folder")

if __name__ == "__main__":
    process_pdf()
