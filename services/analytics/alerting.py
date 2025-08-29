def send_slack_alert(message):
    # Function to send alert to Slack
    import requests
    import json
    import os
    from dotenv import load_dotenv
    from pathlib import Path
    
    # Load .env from project root
    env_path = Path(__file__).resolve().parents[2] / '.env'
    load_dotenv(dotenv_path=env_path)

    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("Warning: SLACK_WEBHOOK_URL not configured")
        return
        
    payload = {
        "text": message
    }
    
    requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})

def send_email_alert(subject, body):
    # Function to send alert via email
    import smtplib
    from email.mime.text import MIMEText

    import os
    from dotenv import load_dotenv
    # Load .env from project root
    from pathlib import Path
    env_path = Path(__file__).resolve().parents[2] / '.env'
    load_dotenv(dotenv_path=env_path)
    
    sender_email = os.getenv("SENDER_EMAIL")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.example.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not all([sender_email, receiver_email, password]):
        print("Warning: Email credentials not fully configured")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())