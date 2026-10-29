import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Humanity Circle Form Handler")

# Load environment configurations
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", SMTP_USER)
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")

# Configure CORS
origins = [
    ALLOWED_ORIGIN,
    "http://localhost:5500",  # VS Code Live Server
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ALLOWED_ORIGIN == "*" else origins,
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


class SubmissionSchema(BaseModel):
    form_type: Optional[str] = "General Submission"
    name: Optional[str] = "Anonymous"
    email: Optional[str] = "Not provided"
    answers: Dict[str, Any]


def send_smtp_email(payload: SubmissionSchema):
    if not SMTP_USER or not SMTP_PASSWORD:
        raise ValueError("SMTP credentials are not configured on the server.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"New Form Submission: {payload.form_type} ({payload.name})"
    msg["From"] = SMTP_USER
    msg["To"] = RECEIVER_EMAIL
    if payload.email and payload.email != "Not provided":
        msg["Reply-To"] = payload.email

    # Plain text version
    text_content = [
        f"Form Type: {payload.form_type}",
        f"Name: {payload.name}",
        f"Email: {payload.email}",
        "\n--- Answers & Details ---",
    ]
    for key, value in payload.answers.items():
        text_content.append(f"{key}: {value}")
    plain_body = "\n".join(text_content)

    # HTML table version
    rows = "".join(
        f"<tr><td style='padding: 8px; border: 1px solid #ddd; font-weight: bold;'>{k}</td>"
        f"<td style='padding: 8px; border: 1px solid #ddd;'>{v}</td></tr>"
        for k, v in payload.answers.items()
    )

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #222;">
        <h2 style="color: #333;">New Submission: {payload.form_type}</h2>
        <p><strong>Name:</strong> {payload.name}</p>
        <p><strong>Email:</strong> {payload.email}</p>
        <h3>Responses:</h3>
        <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
          {rows}
        </table>
      </body>
    </html>
    """

    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, RECEIVER_EMAIL, msg.as_string())


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Backend service is live."}


@app.post("/api/submit", status_code=status.HTTP_200_OK)
def handle_form_submission(data: SubmissionSchema):
    try:
        send_smtp_email(data)
        return {"success": True, "message": "Submission received and email sent."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )