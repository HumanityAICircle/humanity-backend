import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Humanity Circle Form Backend")

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", SMTP_USER)

class SubmissionSchema(BaseModel):
    form_type: Optional[str] = "General Submission"
    name: Optional[str] = "Anonymous"
    email: Optional[str] = "Not provided"
    answers: Dict[str, Any]

def send_smtp_email(payload: SubmissionSchema):
    if not SMTP_USER or not SMTP_PASSWORD:
        raise ValueError("SMTP credentials missing from environment.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"New Form Submission: {payload.form_type} ({payload.name})"
    msg["From"] = SMTP_USER
    msg["To"] = RECEIVER_EMAIL

    rows = "".join(
        f"<tr><td style='padding: 8px; border: 1px solid #ddd; font-weight: bold;'>{k}</td>"
        f"<td style='padding: 8px; border: 1px solid #ddd;'>{v}</td></tr>"
        for k, v in payload.answers.items()
    )

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #222;">
        <h2>New Submission: {payload.form_type}</h2>
        <p><strong>Name:</strong> {payload.name}</p>
        <p><strong>Email:</strong> {payload.email}</p>
        <br>
        <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
          {rows}
        </table>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_content, "html"))

    # Connect to Gmail via SSL (Port 465)
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, RECEIVER_EMAIL, msg.as_string())

@app.get("/")
@app.get("/api")
def home():
    return {"status": "ok", "message": "Backend on Vercel is live."}

@app.post("/api/submit")
@app.post("/submit")
def submit_form(data: SubmissionSchema):
    try:
        send_smtp_email(data)
        return {"success": True, "message": "Submission recorded and email sent."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))