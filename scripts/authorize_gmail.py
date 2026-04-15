import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDS_FILE = r"E:\AI_Employee_Silver_Tier\credentials\credentials.json"
TOKEN_FILE = r"E:\AI_Employee_Silver_Tier\credentials\gmail_token.json"

def authorize():
    flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    Path(TOKEN_FILE).write_text(creds.to_json())
    print(f"Token saved to: {TOKEN_FILE}")
    print("Gmail authorization complete!")

if __name__ == "__main__":
    authorize()
    
