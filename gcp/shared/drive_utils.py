import os
from googleapiclient.errors import HttpError
from shared.auth import get_drive_service

def copy_template_sheet(new_title: str, destination_folder_id: str, template_id: str, creds) -> str:
    """
    Copies a Google Sheet template to a new file in the specified folder.
    """
    try:
        drive = get_drive_service()
        copied_file = drive.files().copy(
            fileId=template_id,
            body={
                "name": new_title,
                "parents": [destination_folder_id]
            }
        ).execute()

        print(f"✅ Copied template to new sheet: https://docs.google.com/spreadsheets/d/{copied_file['id']}")
        return copied_file["id"]

    except HttpError as e:
        print(f"❌ Failed to copy template: {e}")
        raise
