# gaccess

A powerful command-line interface for interacting with Google services (Gmail, Drive, Calendar, Sheets) and AI capabilities using Gemini.

## Features

📌 **Multi-Service Integration**
- Gmail email management
- Google Drive file operations
- Google Calendar event management
- Google Sheets automation
- Google News integration
- Gemini AI integration

📌 **Key Capabilities**
- Email composition and management
- File upload/download from Drive
- Calendar event management with reminders
- Spreadsheet creation and data manipulation
- Voice-activated Google searches
- News fetching from multiple countries
- AI-powered text generation and chat

## Installation

1. **Prerequisites**
- Python 3.9+
- Google account with APIs enabled
- [Create Google Cloud credentials](https://console.cloud.google.com/)

2. **Install dependencies**
```bash
pip install -r requirements.txt


Commands - Purpose - Syntax

Authentication and Session Management

init	Initialize authentication	python gaccess.py init
login	Login with new or existing session	python gaccess.py login [new/existing]
logout	Logout from current session	python gaccess.py logout

Email Management (Gmail)

listemails	List recent emails	python gaccess.py listemails
sendemail	Send an email	python gaccess.py sendemail <to> <subject> <body>
viewemail	View emails from a specific sender	python gaccess.py viewemail <sender_email>

File Management (Google Drive)

listdrive	List files in Google Drive	python gaccess.py listdrive
findfile	Search for a file in Google Drive	python gaccess.py findfile <filename>
downloadfile	Download a file from Google Drive	python gaccess.py downloadfile <filename>
uploadfile	Upload a file to Google Drive	python gaccess.py uploadfile <file_path> [folder_id]

Calendar Management (Google Calendar)

listcalendar	List upcoming calendar events	python gaccess.py listcalendar
addcalendar	Add a new calendar event	python gaccess.py addcalendar <summary> <start_time> <end_time> [description] [location]
deletecalendar	Delete a calendar event	python gaccess.py deletecalendar <event_name>

Google Search and News

search	Perform a Google search	python gaccess.py search <query>
vsearch	Perform a voice-activated search	python gaccess.py vsearch
fetchnews	Fetch news for a specific country	python gaccess.py fetchnews <country_name>

Spreadsheet Management (Google Sheets)

createsheet	Create a new Google Sheet	python gaccess.py createsheet <title>
writesheet	Write data to a Google Sheet	python gaccess.py writesheet <spreadsheet_id> <data>
displaysheet	Display contents of a Google Sheet	python gaccess.py displaysheet <spreadsheet_id>
uploadsheet	Upload a Google Sheet to Drive	python gaccess.py uploadsheet <spreadsheet_id>
summarizesheet	Generate an AI summary of a Google Sheet	python gaccess.py summarizesheet <spreadsheet_id>

AI Features (Gemini)

gemini	Start an interactive chat with Gemini AI	python gaccess.py gemini
prompt	Generate text using Gemini AI	python gaccess.py prompt <your_prompt>
