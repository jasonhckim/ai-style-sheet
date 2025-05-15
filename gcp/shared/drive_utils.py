from shared.auth import get_drive_service

def copy_template_sheet(new_title, destination_folder_id, template_id, creds):
    drive = get_drive_service()
    copied_file = drive.files().copy(
        fileId=template_id,
        body={"name": new_title, "parents": [destination_folder_id]}
    ).execute()
    return copied_file["id"]
