import os
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

FOLDER_ID = "18i3g2ZOSDMbaxBsYs5OGtOmedZYoFX30"

def get_credentials():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    creds.refresh(Request())
    return creds

def list_files(service):
    files, page_token = [], None
    while True:
        resp = service.files().list(
            q=f"'{FOLDER_ID}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            pageToken=page_token,
        ).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return sorted(files, key=lambda f: f["name"].lower())

def file_url(f):
    mime = f["mimeType"]
    fid = f["id"]
    if mime == "application/vnd.google-apps.document":
        return f"https://docs.google.com/document/d/{fid}/edit"
    if mime == "application/vnd.google-apps.spreadsheet":
        return f"https://docs.google.com/spreadsheets/d/{fid}/edit"
    return f"https://drive.google.com/file/d/{fid}/view"

def generate_html(files):
    rows = "\n".join(
        f'    <tr><td><a href="{file_url(f)}" target="_blank">{f["name"]}</a></td>'
        f'<td>{f.get("modifiedTime", "")[:10]}</td></tr>'
        for f in files
    )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Document Library</title>
  <style>
    body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}
    h1 {{ font-size: 1.4rem; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #ddd; }}
    th {{ background: #f5f5f5; font-weight: 600; }}
    a {{ color: #1a73e8; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .meta {{ color: #888; font-size: 0.85rem; margin-top: 1.5rem; }}
  </style>
</head>
<body>
  <h1>Document Library</h1>
  <table>
    <thead><tr><th>File</th><th>Modified</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>
  <p class="meta">Last updated: {now}</p>
</body>
</html>"""

if __name__ == "__main__":
    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)
    files = list_files(service)
    html = generate_html(files)
    os.makedirs("_site", exist_ok=True)
    with open("_site/index.html", "w") as fh:
        fh.write(html)
    print(f"Generated index with {len(files)} files")
