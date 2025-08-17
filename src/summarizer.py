import os
from dotenv import load_dotenv
from google import genai
import json
from datetime import datetime

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def summarize_email(email_data):
    prompt = """
    You are an AI assistant that processes a day's worth of emails. 
    You must classify and summarize them into two groups:
    1. Urgent Emails (requiring immediate action).
    2. Digest Emails (summarized for an end-of-day digest).

    Rules:
    - Urgent Emails:
      - Criteria: deadlines within 24 hours, time-sensitive tasks, critical blockers, or explicitly marked urgent.
      - Include: sender, subject, summary (2–3 sentences), action_items, deadline.
    - General Emails:
      - Group into: high_priority (important but not urgent today), updates (informative, FYIs), low_priority (newsletters, promotions).
      - Each entry: sender, subject, summary (1–3 sentences), action_items (or "none").
    - End with next_steps: consolidated list of action items from all emails.
    - If a category has no emails, return [] (empty array).
    - Output must be valid JSON only. No other extra commentary. 

    JSON format:
    {
      "urgent_emails": [ { ... } ],
      "general_emails": {
        "high_priority": [ { ... } ],
        "updates": [ { ... } ],
        "low_priority": [ { ... } ]
      },
      "next_steps": [ ... ]
    }
    
    Email data to process:
    """ + email_data
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        output = response.text
        
        # parse the output as JSON
        try:
            json_start = output.find('{')
            json_end = output.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = output[json_start:json_end]
                parsed_json = json.loads(json_str)
                return parsed_json
            else:
                print("No valid JSON found in output")
                return None
        except json.JSONDecodeError as json_error:
            print(f"Failed to parse JSON: {json_error}")
            print(f"Raw output: {output}")
            return None
            
    except Exception as e:
        print(f"Error summarizing email: {e}")
        return None
    
def format_response(response, section):
    formatted_output = []
    
    # Urgent Emails Section
    if 'urgent_emails' in response and response['urgent_emails'] and section == 'urgent_emails':
        formatted_output.append(f"\n🚨 URGENT ({len(response['urgent_emails'])}):")
        formatted_output.append("-" * 30)
        for i, email in enumerate(response['urgent_emails'], 1):
            formatted_output.append(f"{i}. From: {email['sender']}")
            formatted_output.append(f"   Subject: {email['subject']}")
            formatted_output.append(f"   Summary: {email['summary']}")
            formatted_output.append(f"   Action: {email['action_items']}")
            if 'deadline' in email:
                formatted_output.append(f"   Deadline: {email['deadline']}")
            formatted_output.append("")
    
    # General Emails Section
    if 'general_emails' in response and section == 'general_emails':
        digest = response['general_emails']
        
        # High Priority
        if digest.get('high_priority'):
            formatted_output.append(f"\n🔺 HIGH PRIORITY ({len(digest['high_priority'])}):")
            formatted_output.append("-" * 20)
            for i, email in enumerate(digest['high_priority'], 1):
                formatted_output.append(f"{i}. From: {email['sender']}")
                formatted_output.append(f"   Subject: {email['subject']}")
                formatted_output.append(f"   Summary: {email['summary']}")
                formatted_output.append(f"   Action: {email['action_items']}")
                formatted_output.append("")
        
        # Updates
        if digest.get('updates'):
            formatted_output.append(f"\n🌐 GENERAL UPDATES ({len(digest['updates'])}):")
            formatted_output.append("-" * 25)
            for i, email in enumerate(digest['updates'], 1):
                formatted_output.append(f"{i}. From: {email['sender']}")
                formatted_output.append(f"   Subject: {email['subject']}")
                formatted_output.append(f"   Summary: {email['summary']}")
                if email['action_items'] != 'none':
                    formatted_output.append(f"   Action: {email['action_items']}")
                formatted_output.append("")
        
        # Low Priority
        if digest.get('low_priority'):
            formatted_output.append(f"\n🔻 LOW PRIORITY ({len(digest['low_priority'])}):")
            formatted_output.append("-" * 22)
            for i, email in enumerate(digest['low_priority'], 1):
                formatted_output.append(f"{i}. From: {email['sender']}")
                formatted_output.append(f"   Subject: {email['subject']}")
                formatted_output.append(f"   Summary: {email['summary']}")
                if email['action_items'] != 'none':
                    formatted_output.append(f"   Action: {email['action_items']}")
                formatted_output.append("")
    
    # Next Steps Section
    if 'next_steps' in response and response['next_steps'] and section == 'next_steps':
        formatted_output.append(f"\n✅ NEXT STEPS:")
        formatted_output.append("-" * 15)
        for i, step in enumerate(response['next_steps'], 1):
            formatted_output.append(f"{i}. {step}")
    
    return "\n".join(formatted_output)
        
    
