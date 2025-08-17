from dotenv import load_dotenv
import os
import requests
from email_reader import set_connection, get_unread_emails_today, get_email_data
from summarizer import summarize_email, format_response

load_dotenv()

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

def send_to_discord(message):
    payload = {
        "content": message
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload)
    except Exception as e:
        print(f"Failed to send Discord message: {e}")

def main():
    service = set_connection()
    today_emails = get_unread_emails_today(service)
    
    if not today_emails:
        message = f"📭 **No emails for today**"
        send_to_discord(message)
        return
    
    # process all unread emails that were sent today and collect their data
    all_email_data = []
    for email in today_emails:
        email_data = get_email_data(service, email["id"])
        if email_data:
            all_email_data.append(email_data)
    
    # convert to string format for processing
    email_data_str = "\n\n".join([
        f"From: {email.get('from', 'Unknown')}\n"
        f"Subject: {email.get('subject', 'No Subject')}\n"
        f"Content: {email.get('text', 'No content')}"
        for email in all_email_data
    ])
    
    summary = summarize_email(email_data_str)
    
    # handle each section separately because of message length limit
    urgent_emails = format_response(summary, 'urgent_emails')
    general_emails = format_response(summary, 'general_emails')
    next_steps = format_response(summary, 'next_steps')
    
    # send the formatted summary to discord
    send_to_discord(urgent_emails)
    send_to_discord(general_emails)
    send_to_discord(next_steps)

if __name__ == "__main__":
    main()