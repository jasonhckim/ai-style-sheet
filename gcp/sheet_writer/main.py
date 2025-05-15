from shared import auth, drive_utils
import functions_framework
import json
import gspread
import pandas as pd

@functions_framework.cloud_event
def main(cloud_event):
    message = cloud_event.data["message"]
    payload = json.loads(base64.b64decode(message["data"]).decode("utf-8"))

    creds = auth.get_creds()
    client = gspread.authorize(creds)

    # Copy template
    sheet_id = drive_utils.copy_sheet_from_template(payload["file_name"].replace(".pdf", ""), payload["folder_id"], creds)
    sheet = client.open_by_key(sheet_id)

    # Convert to DataFrame
    df = pd.DataFrame([payload])

    # Upload to Sheet1
    sheet.sheet1.clear()
    sheet.sheet1.update(values=[df.columns.tolist()] + df.values.tolist())

    print(f"✅ Sheet updated: https://docs.google.com/spreadsheets/d/{sheet_id}")
