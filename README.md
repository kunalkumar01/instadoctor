# Insta Doctor

Insta Doctor is a simple Flask application that provides an **AI-powered** medical chat assistant.

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Setup

1. Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

2. Set the following environment variables:

- `OPENAI_API_KEY` – API key for OpenAI.
- `ASSISTANT_ID` – ID of the assistant you created on OpenAI.
- `SECRET_KEY` – Secret key used by Flask for sessions.

3. Run the application locally:

```bash
python app.py
```

The server will start on `http://localhost:8080` and you can navigate to `/chat` to start chatting.

### Accounts

Users can sign up or log in before chatting. Accounts are stored in a local SQLite database (`instadoctor.db`). If you send more than three messages without an account you will be asked to log in.

### Daily Limit

Guests can only send up to three messages per day before being prompted to sign in or create an account.

### Medical Intake

When you first visit `/chat` you will be redirected to `/intake` to provide
basic information like name, age, gender, symptoms and duration. This data is
sent to the assistant only once at the beginning of the conversation so it can
better tailor its responses.

### Uploading Files

On the chat page you can optionally upload PDF or image files (such as lab
results) using the file input below the message box. Uploaded files are attached
to your session's conversation thread and are accessible to the OpenAI assistant
for reference in subsequent replies.

