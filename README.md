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

init	Initialize authentication	gaccess init
login	Login with new or existing session	gaccess login [new/existing]
logout	Logout from current session	gaccess logout

Email Management (Gmail)

listemails	List recent emails	gaccess listemails
sendemail	Send an email	gaccess sendemail <to> <subject> <body>
viewemail	View emails from a specific sender	gaccess viewemail <sender_email>

File Management (Google Drive)

listdrive	List files in Google Drive	gaccess listdrive
findfile	Search for a file in Google Drive	gaccess findfile <filename>
downloadfile	Download a file from Google Drive	gaccess downloadfile <filename>
uploadfile	Upload a file to Google Drive	gaccess uploadfile <file_path> [folder_id]

Calendar Management (Google Calendar)

listcalendar	List upcoming calendar events	gaccess listcalendar
addcalendar	Add a new calendar event	gaccess addcalendar <summary> <start_time> <end_time> [description] [location]
deletecalendar	Delete a calendar event	gaccess deletecalendar <event_name>

Google Search and News

search	Perform a Google search	gaccess search <query>
vsearch	Perform a voice-activated search	gaccess vsearch
fetchnews	Fetch news for a specific country	gaccess fetchnews <country_name>

Spreadsheet Management (Google Sheets)

createsheet	Create a new Google Sheet	gaccess createsheet <title>
writesheet	Write data to a Google Sheet	gaccess writesheet <spreadsheet_id> <data>
displaysheet	Display contents of a Google Sheet	gaccess displaysheet <spreadsheet_id>
uploadsheet	Upload a Google Sheet to Drive	gaccess uploadsheet <spreadsheet_id>
summarizesheet	Generate an AI summary of a Google Sheet	gaccess summarizesheet <spreadsheet_id>

AI Features (Gemini)

gemini	Start an interactive chat with Gemini AI	gaccess gemini
prompt	Generate text using Gemini AI	gaccess prompt <your_prompt>
