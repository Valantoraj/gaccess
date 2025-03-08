import os
import sys
import feedparser
import json
import argparse
import requests
import speech_recognition as sr
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload,MediaIoBaseDownload
from googleapiclient.discovery import build
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from transformers import pipeline
import datetime
import time
import pytz
import threading
from googleapiclient.discovery import build
from win10toast import ToastNotifier 
import pythoncom

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send",'https://www.googleapis.com/auth/calendar','https://www.googleapis.com/auth/calendar.events',"https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
SESSION_TOKEN_FILE = r"C:\Users\valan\gaccess\session_token.json"
PERSISTENT_TOKEN_FILE = r"C:\Users\valan\gaccess\token.json"
CREDENTIALS_FILE = r"C:\Users\valan\gaccess\credentials.json"
API_KEY_FILE = r"C:\Users\valan\gaccess\apikey.json"

with open(API_KEY_FILE, "r") as f:
    api_data = json.load(f)
    API_KEY = api_data["API_KEY"]
    CX = api_data["CX"]

SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

def login(mode="existing"):
    creds = None
    if mode == "existing":
        if os.path.exists(SESSION_TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(SESSION_TOKEN_FILE)
        elif os.path.exists(PERSISTENT_TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(PERSISTENT_TOKEN_FILE)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if mode == "new":
                if os.path.exists(SESSION_TOKEN_FILE): os.remove(SESSION_TOKEN_FILE)
                if os.path.exists(PERSISTENT_TOKEN_FILE): os.remove(PERSISTENT_TOKEN_FILE)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(SESSION_TOKEN_FILE, "w") as session_token:
            session_token.write(creds.to_json())
        with open(PERSISTENT_TOKEN_FILE, "w") as persistent_token:
            persistent_token.write(creds.to_json())
    print("✅ Authentication Successful!")
    return creds

def logout():
    if os.path.exists(SESSION_TOKEN_FILE):
        os.remove(SESSION_TOKEN_FILE)
        print("🔴 Logged out from current session.")
    else:
        print("⚠ No active session found.")

def google_search(query):
    params = {"key": API_KEY, "cx": CX, "q": query}
    response = requests.get(SEARCH_URL, params=params)
    results = response.json().get("items", [])
    if results:
        print(f"\n🔎 Search Results for: {query}\n")
        for idx, item in enumerate(results[:5]):
            print(f"{idx+1}. {item['title']}\n   {item['link']}\n")
    else:
        print("❌ No results found.")

def voice_search():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Speak your search query...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            query = recognizer.recognize_google(audio)
            print(f"✅ You said: {query}")
            google_search(query)
        except sr.UnknownValueError:
            print("❌ Could not understand the audio. Please try again.")
        except sr.RequestError:
            print("❌ Could not request results from Google Speech API.")

summarizer = pipeline("summarization", model="t5-small", tokenizer="t5-small")

def summarize_text(text, max_length=80):
    if len(text.split()) < 10:
        return text
    summary = summarizer(text, max_length=max_length, min_length=30, do_sample=False)
    return summary[0]['summary_text']
def get_gmail_service():
    creds = login()
    return build("gmail", "v1", credentials=creds)

def get_email_body(msg_detail):
    payload = msg_detail["payload"]
    
    if "body" in payload and "data" in payload["body"]:
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    
    elif "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain" and "data" in part["body"]:
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
    
    return "No full body available."

def list_emails():
    service = get_gmail_service()

    email_types = {
        "INBOX": "📥 Inbox",
        "SENT": "📤 Sent",
        "DRAFT": "📝 Drafts"
    }

    for label, label_name in email_types.items():
        print(f"\n{label_name}\n" + "═" * 80)
        results = service.users().messages().list(userId="me", labelIds=[label], maxResults=5).execute()
        messages = results.get("messages", [])

        if not messages:
            print("No emails found.\n")
            continue

        for msg in messages:
            msg_detail = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            headers = msg_detail["payload"].get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
            body = get_email_body(msg_detail)  
            summary = summarize_text(body[:512])

            print("--------------------------------------------------")
            print(f"🔹 Sender: {sender[:50]}")
            print(f"   Subject: {subject[:50]}")
            print(f"   Summary: {summary}")
            print(f"   ID: {msg['id']}")
        print("--------------------------------------------------\n")

def view_email(sender_email):
    service = get_gmail_service()
    
    query = f'from:{sender_email}'
    results = service.users().messages().list(userId="me", q=query, maxResults=10).execute()
    
    if "messages" not in results:
        print(f"❌ No emails found from {sender_email}")
        return
    
    print(f"📨 Retrieving emails from {sender_email}...\n")
    
    for index, msg in enumerate(results["messages"], start=1):
        email_id = msg["id"]
        msg_detail = service.users().messages().get(userId="me", id=email_id).execute()
        
        headers = msg_detail["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "📭 No Subject")
        body = get_email_body(msg_detail)  
        summary = summarize_text(body[:512])

        print(f"📧 Email {index}")
        print(f"   📌 Subject: {subject}")
        print(f"   📝 Summary: {summary}")
        print(f"   🔗 [View Full Email](https://mail.google.com/mail/u/0/#inbox/{email_id})") 
        print("—" * 50)  


def send_email(to, subject, body):
    service = get_gmail_service()
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    send_request = {"raw": encoded_message}
    service.users().messages().send(userId="me", body=send_request).execute()
    print(f"📨 Email sent to {to} successfully!")

def get_drive_service():
    creds = login()
    return build("drive", "v3", credentials=creds)

def list_drive_files():
    service = get_drive_service()
    results = service.files().list(fields="files(id, name, mimeType)").execute()
    files = results.get("files", [])

    if not files:
        print("📂 No files found in Google Drive.")
        return

    print("\n📂 Google Drive Files & Folders:\n")
    for file in files:
        icon = "📁" if file["mimeType"] == "application/vnd.google-apps.folder" else "📄"
        print(f"{icon} {file['name']}  | 🆔 {file['id']}  | 📌 Type: {file['mimeType']}")


def get_drive_service():
    creds = login()
    return build("drive", "v3", credentials=creds)

def find_drive_file(name):
    service = get_drive_service()
    query = f"name = '{name}'"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    files = results.get("files", [])
    
    if files:
        for file in files:
            print(f"✅ Found: {file['name']} (ID: {file['id']}, Type: {file['mimeType']})")
        return files[0]
    else:
        print("❌ No file or folder found with that name.")
        return None

def resolve_shortcut(file):
    service = get_drive_service()
    if file["mimeType"] == "application/vnd.google-apps.shortcut":
        shortcut_id = file["id"]
        shortcut_info = service.files().get(fileId=shortcut_id, fields="shortcutDetails").execute()
        return shortcut_info["shortcutDetails"]["targetId"]
    return file["id"]

def download_drive_file(name, destination_folder=None):
    if destination_folder is None:
        destination_folder = os.path.expanduser("~/Downloads")

    file = find_drive_file(name)
    if not file:
        return
    
    file_id = resolve_shortcut(file)
    service = get_drive_service()

    export_formats = {
        "application/vnd.google-apps.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    }

    if file["mimeType"] in export_formats:
        mime_type = export_formats[file["mimeType"]]
        request = service.files().export_media(fileId=file_id, mimeType=mime_type)
        file_extension = {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.openxmlformats-officedocument.spreadsheet": ".xlsx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx"
        }[mime_type]
        file_path = os.path.join(destination_folder, name + file_extension)
    else:
        request = service.files().get_media(fileId=file_id)
        file_path = os.path.join(destination_folder, name)

    os.makedirs(destination_folder, exist_ok=True)

    with open(file_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"⬇️ Download Progress: {int(status.progress() * 100)}%")

    print(f"✅ File '{name}' downloaded to '{destination_folder}'")

def upload_drive_file(file_path, folder_id=None):
    service = get_drive_service()
    
    file_metadata = {"name": os.path.basename(file_path)}
    if folder_id:
        file_metadata["parents"] = [folder_id]
    
    media = MediaFileUpload(file_path, resumable=True)
    
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    print(f"✅ File '{file_path}' uploaded successfully with ID: {file.get('id')}")


if not API_KEY:
    print("❌ Error: API key not found in apikey.json. Make sure the key is stored as {'api_key': 'YOUR_KEY'}.")
    exit(1)

genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-1.5-pro-latest"

def generate_text(prompt):
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

def interactive_chat():
    print("\n🔹 Welcome to Gemini AI CLI Chat! Type 'exit' to quit. 🔹\n")
    
    try:
        while True:
            user_input = input("📝 You: ")

            if user_input.lower() in ["exit", "quit"]:
                print("\n👋 Exiting chat. Have a great day!")
                break
            print("\n🧠 Gemini AI Response:\n")
            print(generate_text(user_input))

    except KeyboardInterrupt:
        print("\n\n👋 Chat session ended. Goodbye!")

def get_calendar_service():
    creds = login()
    return build("calendar", "v3", credentials=creds)


def get_gmail_service():
    creds = login()
    return build('gmail', 'v1', credentials=creds)

def list_calendar_events():
    service = get_calendar_service()
    calendar_list = service.calendarList().list().execute()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print("\n📅 Upcoming Events:\n" + "=" * 50)
    events_result = service.events().list(calendarId=calendar_list["items"][0]["id"], timeMin=now, maxResults=5, singleEvents=True, orderBy="startTime").execute()
    events = events_result.get("items", [])

    if not events:
        print("❌ No upcoming events found.")
        return

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        print(f"📌 {event['summary']} 🕒 {start}")

    print("=" * 50)


def delete_calendar_event(event_name):
    service = get_calendar_service()
    events = service.events().list(calendarId="primary").execute().get("items", [])

    for event in events:
        if event["summary"].lower() == event_name.lower():
            service.events().delete(calendarId="primary", eventId=event["id"]).execute()
            print(f"🗑 Event '{event_name}' deleted successfully!")
            return
    print(f"❌ Event '{event_name}' not found.")


def add_calendar_event_with_reminders(summary, start_time, end_time, description="", location=""):
    service = get_calendar_service()
    
    ist = pytz.timezone("Asia/Kolkata")
    
    start_dt = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
    start_dt = ist.localize(start_dt)

    end_dt = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")
    end_dt = ist.localize(end_dt)
    
    reminders = [
        {"method": "popup", "minutes": 4320},
        {"method": "popup", "minutes": 1440},
        {"method": "popup", "minutes": 0},
    ]
    
    event = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        "reminders": {
            "useDefault": False,
            "overrides": reminders
        }
    }
    
    event = service.events().insert(calendarId="primary", body=event).execute()
    print(f"✅ Event created: {event.get('htmlLink')}")

    send_event_email_reminders(event)

def send_event_email_reminders(event):
    service = get_gmail_service()
    profile = service.users().getProfile(userId='me').execute()
    event_summary = event.get('summary')
    event_start_time = event.get('start').get('dateTime')
    
    subject = f"Reminder: {event_summary} is coming up"
    body = f"""
    <html>
  <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 30px; background-color: #f8f9fa; color: #333;">
    <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
      
      <h2 style="color: #2d3436; font-size: 24px; font-weight: 600; margin-bottom: 20px;">Event Reminder: <span style="color: #1abc9c;">{event_summary}</span></h2>
      
      <p style="font-size: 16px; color: #2c3e50;">Dear Recipient,</p>
      
      <p style="font-size: 16px; color: #7f8c8d; line-height: 1.6;">
        We would like to remind you that your upcoming event, <strong style="color: #1abc9c;">{event_summary}</strong>, will begin at <strong style="color: #1abc9c;">{event_start_time}</strong>.
      </p>
      
      <p style="font-size: 16px; color: #7f8c8d; line-height: 1.6;"> 
        Please make sure to mark your calendar and prepare accordingly. If you need to make any changes or need further details, feel free to contact us.
      </p>
      
      <p style="font-size: 16px; color: #2c3e50; font-weight: 600;">Don't forget to attend the event on time!</p>

      <div style="margin-top: 30px; text-align: center; font-size: 12px; color: #95a5a6;">
        <footer>
          This is an automated reminder email.
        </footer>
      </div>
      
    </div>
  </body>
</html>
    """

    send_email(service,profile['emailAddress'], subject, body)

def send_email(service, to, subject, body):
    message = MIMEMultipart()
    message["to"] = to
    message["subject"] = subject
    msg = MIMEText(body, "html")
    message.attach(msg)

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    send_request = {"raw": encoded_message}
    service.users().messages().send(userId="me", body=send_request).execute()
    print("Email successfully sent!")


def get_google_news_rss(country_code):
    return f'https://news.google.com/rss?hl=en-{country_code}&gl={country_code}&ceid={country_code}:en'

def fetch_news(country_code, max_articles=15):
    url = get_google_news_rss(country_code)
    feed = feedparser.parse(url)
    news_items = []
    
    for entry in feed.entries[:max_articles]:
        news_items.append({
            'title': entry.title,
            'link': entry.link
        })
    
    return news_items

def display_news(news_list, country_name):
    print(f"\n📰 Top News in {country_name}:\n")
    print("=" * 80)
    for idx, news in enumerate(news_list, start=1):
        print(f"🔹 {idx}. {news['title']}")
        print(f"   🔗 {news['link']}")
        print("-" * 80)
    print("\n")


def get_sheets_service():
    creds = login()
    return build("sheets", "v4", credentials=creds)

def create_sheet(service, title):
    try:
        spreadsheet = {
            "properties": {
                "title": title
            }
        }
        spreadsheet = service.spreadsheets().create(body=spreadsheet, fields="spreadsheetId").execute()
        print(f"✅ Created Google Sheet: {title}")
        return spreadsheet.get("spreadsheetId")
    except HttpError as error:
        print(f"❌ An error occurred: {error}")
        return None

def write_to_sheet(service, spreadsheet_id, range_name, values):
    try:
        body = {
            "values": values
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        print(f"✅ Updated {result.get('updatedCells')} cells.")
    except HttpError as error:
        print(f"❌ An error occurred: {error}")

def display_sheet_contents(sheets_service, spreadsheet_id):
    try:
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            fields="sheets(properties(title))"
        ).execute()
        
        sheet_title = spreadsheet["sheets"][0]["properties"]["title"]
        
        range_name = f"{sheet_title}!A:Z"
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            print("📄 The sheet is empty.")
            return
        
        print(f"\n📄 Contents of Sheet '{spreadsheet_id}':\n")
        for row in values:
            print(" | ".join(row))
    except HttpError as error:
        print(f"❌ An error occurred: {error}")

def upload_sheet_to_drive(drive_service, spreadsheet_id):
    try:
        file = drive_service.files().get(fileId=spreadsheet_id, fields='id, name').execute()
        file_name = file['name']
        
        copied_file = drive_service.files().copy(
            fileId=spreadsheet_id,
            body={"name": file_name}
        ).execute()
        
        print(f"✅ Google Sheet '{file_name}' uploaded to Google Drive.")
        print(f"🔗 File ID: {copied_file['id']}")
    except HttpError as error:
        print(f"❌ An error occurred: {error}")

def fetch_sheet_content(sheets_service, spreadsheet_id):
    try:
        range_name = "Sheet1!A:Z"
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return "The sheet is empty."
        
        content = "\n".join([", ".join(row) for row in values])
        return content
    except HttpError as error:
        return f"❌ An error occurred while fetching sheet content: {error}"

def get_sheet_summary(sheets_service, spreadsheet_id):
    content = fetch_sheet_content(sheets_service, spreadsheet_id)
    
    if content.startswith("❌"):
        print(content)
        return
    
    prompt = f"Tell what this sheets is about and summarize the following data from a Google Sheet:\n\n{content}"
    summary = generate_text(prompt)
    
    print("\nSummary of the Sheet:\n")
    print(summary)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Access CLI Tool")
    parser.add_argument("command", type=str, help="Command (init, login, logout, search, vsearch, listemails, sendemail, fetchnews)")
    parser.add_argument("extra", nargs="*", type=str, help="Additional arguments")
    args = parser.parse_args()
    
    command = args.command.lower()
    
    if command == "init":
        login()
    elif command == "login":
        mode = args.extra[0].lower() if args.extra else None
        login(mode if mode in ["new", "existing"] else "existing")
    elif command == "logout":
        logout()
    elif command == "search":
        google_search(" ".join(args.extra) if args.extra else "")
    elif command == "vsearch":
        voice_search()
    elif command == "listemails":
        list_emails()
    elif command == "sendemail":
        if len(args.extra) < 3:
            print("❌ Usage: gaccess sendemail <to> <subject> <body>")
        else:
            send_email(args.extra[0], args.extra[1], " ".join(args.extra[2:]))
    elif command == "viewemails":
        if len(args.extra) < 1:
            print("❌ Usage: gaccess viewemail <email_id>")
        else:
            view_email(args.extra[0])
    elif command == "listdrive":
        list_drive_files()
    elif command == "findfile":
        if args.extra:
            find_drive_file(" ".join(args.extra))
        else:
            print("❌ Usage: gaccess findfile <filename>")
    elif command == "downloadfile":
        if args.extra:
            download_drive_file(" ".join(args.extra))
        else:
            print("❌ Usage: gaccess downloadfile <filename>")
    elif command == "uploadfile":
        if len(args.extra) < 1:
            print("❌ Usage: gaccess uploadfile <file_path> [folder_id]")
        else:
            upload_drive_file(args.extra[0], args.extra[1] if len(args.extra) > 1 else None)
    elif command == "gemini":
        interactive_chat()
    elif command == "prompt":
        if not args.extra:
            print("❌ Error: Please provide a prompt for text generation.")
        else:
            print("\n🧠 Gemini AI Response:\n")
            print(generate_text(" ".join(args.extra)))
    elif command == "listcalendar":
        list_calendar_events()
    elif command == "addcalendar":
        if len(args.extra) < 3:
            print("❌ Usage: gaccess addcalendar <summary> <start_time> <end_time>")
        else:
            add_calendar_event_with_reminders(args.extra[0], args.extra[1], args.extra[2], " ".join(args.extra[3:]))
    elif command == "deletecalendar":
        if len(args.extra) < 1:
            print("❌ Usage: gaccess deletecalendar <event_name>")
        else:
            delete_calendar_event(args.extra[0])
    elif command == "fetchnews":
        if len(args.extra) < 1:
            print("❌ Usage: gaccess fetchnews <country_name>")
        else:
            country_name = args.extra[0]
            country_codes = {
                'India': 'IN',
                'United States': 'US',
                'United Kingdom': 'GB',
                'Australia': 'AU',
                'Canada': 'CA',
                'Germany': 'DE',
                'France': 'FR',
                'Italy': 'IT',
                'Spain': 'ES',
                'Brazil': 'BR',
                'Mexico': 'MX',
                'Japan': 'JP',
                'China': 'CN',
                'South Korea': 'KR',
                'Russia': 'RU',
                'South Africa': 'ZA',
                'Saudi Arabia': 'SA',
                'United Arab Emirates': 'AE',
                'Argentina': 'AR',
                'Indonesia': 'ID'
            }
            
            if country_name not in country_codes:
                print("❌ Invalid country name. Please check the available list and try again.")
            else:
                news_list = fetch_news(country_codes[country_name])
                display_news(news_list, country_codes[country_name])
    elif command == "createsheet":
        if len(args.extra) < 1:
            print("❌ Usage: gaccess createsheet <title>")
        else:
            service = get_sheets_service()
            title = args.extra[0]
            spreadsheet_id = create_sheet(service, title)
            if spreadsheet_id:
                print(f"🔗 Spreadsheet ID: {spreadsheet_id}")
    elif command == "writesheet":
        if len(args.extra) < 2:
            print("❌ Usage: gaccess writesheet <spreadsheet_id> <data>")
        else:
            service = get_sheets_service()
            spreadsheet_id = args.extra[0]
            range_name = "Sheet1!A1"
            values = [row.split(",") for row in args.extra[1:]]
            write_to_sheet(service, spreadsheet_id, range_name, values)
    elif command == "displaysheet":
        if len(args.extra) < 1:
            print("❌ Usage: gaccess displaysheet <spreadsheet_id>")
        else:
            sheets_service = get_sheets_service()
            spreadsheet_id = args.extra[0]
            display_sheet_contents(sheets_service, spreadsheet_id)
    elif command == "uploadsheet":
        if len(args.extra) < 1:
            print("❌ Usage: gaccess uploadsheet <spreadsheet_id>")
        else:
            drive_service = get_drive_service()
            spreadsheet_id = args.extra[0]
            upload_sheet_to_drive(drive_service, spreadsheet_id)
    elif command == "summarizesheet":
        if len(args.extra) < 1:
            print("❌ Usage: gaccess summarizesheet <spreadsheet_id>")
        else:
            sheets_service = get_sheets_service()
            spreadsheet_id = args.extra[0]
            get_sheet_summary(sheets_service, spreadsheet_id)
    else:
        print(f"❌ Unknown command: {command}")