# src/youtube_auth.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


DEFAULT_SCOPES: Sequence[str] = ("https://www.googleapis.com/auth/youtube.upload",)


def get_youtube_service(
    client_secrets_path: str,
    token_path: str,
    scopes: Sequence[str] = DEFAULT_SCOPES,
):
    """
    Returns an authenticated YouTube API client.
    - First run: opens browser for consent, saves token to token_path.
    - Next runs: reuses token and refreshes automatically when needed.
    """
    token_file = Path(token_path)
    creds: Credentials | None = None

    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, scopes)
            creds = flow.run_local_server(port=0)

        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")

    return build("youtube", "v3", credentials=creds)
