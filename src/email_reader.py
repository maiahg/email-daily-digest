import os.path
import base64
import re

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def set_connection():
  creds = None

  parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  
  credentials_path = os.path.join(parent_dir, "credentials.json")
  token_path = os.path.join(parent_dir, "token.json")
  
  if os.path.exists(token_path):
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          credentials_path, SCOPES
      )
      creds = flow.run_local_server(port=0)
    with open(token_path, "w") as token:
      token.write(creds.to_json())
  return build("gmail", "v1", credentials=creds)


def get_unread_emails_today(service):
  try:
    today = datetime.now().strftime("%Y-%m-%d")
    query = f"after:{today} is:unread is:inbox"
    results = service.users().messages().list(userId="me", q=query).execute()
    return results.get("messages", [])
  except HttpError as error:
    print(f"An error occurred: {error}")

def get_email_data(service, email_id):
  try:
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=email_id, format="full")
        .execute()
    )
    payload = msg["payload"]
    headers = payload["headers"]

    email_data = process_headers(headers)
    email_data["id"] = email_id

    parts = payload.get("parts")
    data = get_parts(parts)
    email_data["text"] = " ".join(data)

    return email_data
  except HttpError as error:
    print(f"An error occurred: {error}")

def process_headers(headers):
    email_data = {}
    for header in headers:
        name = header["name"]
        value = header["value"]
        if name.lower() in ["from", "subject"]:
            email_data[name.lower()] = value
    return email_data

def get_parts(parts):
    data = []
    if parts:
        for part in parts:
            body = part.get("body")
            data_part = body.get("data")
            if part.get("parts"):
                data += get_parts(part.get("parts"))
            if data_part:
                text = decode_body(data_part)
                data.append(text)
    return data

def decode_body(data):
    decoded_data = base64.urlsafe_b64decode(data).decode("utf-8")
    soup = BeautifulSoup(decoded_data, "html.parser")
    return clean_text(soup.get_text())
  
def clean_text(text):
    # remove links
    text = re.sub(r'\(https?://[^)]+\)', '', text)
    text = re.sub(r'https?://\S+', '', text)
    
    # remove empty parentheses that might be left behind
    text = re.sub(r'\(\s*\)', '', text)
    
    # remove new lines
    text = text.replace('\n', '')
    
    # remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    
    # remove images
    text = re.sub(r'\[image[^\]]*\]', '', text)
    
    # remove half spaces (\u200c)
    text = re.sub(r'\u200c', '', text)
    
    # remove non-breaking spaces (\u00a0)
    text = re.sub(r'\u00a0', '', text)
    
    return text.strip()