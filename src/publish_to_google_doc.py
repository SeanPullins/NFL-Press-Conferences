import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/documents"]
DIGEST_PATH = Path("data/reports/notebooklm-digest.md")


def get_credentials():
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is required to publish to Google Docs.")

    info = json.loads(raw)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def get_document_end_index(service, doc_id: str) -> int:
    doc = service.documents().get(documentId=doc_id).execute()
    body = doc.get("body", {}).get("content", [])
    if not body:
        return 1
    return body[-1].get("endIndex", 1)


def publish_digest_to_google_doc():
    doc_id = os.getenv("GOOGLE_DOC_ID")
    if not doc_id:
        raise RuntimeError("GOOGLE_DOC_ID is required to publish to Google Docs.")

    if not DIGEST_PATH.exists():
        raise RuntimeError(f"Digest file not found: {DIGEST_PATH}")

    text = DIGEST_PATH.read_text(encoding="utf-8")
    if not text.strip():
        text = "NFL Press Conference Digest\n\nNo digest content was generated in this run."

    credentials = get_credentials()
    service = build("docs", "v1", credentials=credentials)

    end_index = get_document_end_index(service, doc_id)
    requests = []

    if end_index > 2:
        requests.append({
            "deleteContentRange": {
                "range": {
                    "startIndex": 1,
                    "endIndex": end_index - 1,
                }
            }
        })

    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": text,
        }
    })

    service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests},
    ).execute()

    print(f"Published digest to Google Doc: {doc_id}")


if __name__ == "__main__":
    publish_digest_to_google_doc()
