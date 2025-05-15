from google.cloud import secretmanager

def access_secret(secret_name: str, project_id: str):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    return client.access_secret_version(request={"name": name}).payload.data.decode("UTF-8")
