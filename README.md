# Insta Doctor

Insta Doctor is a simple Flask application that provides an AI powered medical chat assistant.

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

