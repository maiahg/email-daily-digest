import os
from dotenv import load_dotenv
from google import genai
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def summarize_email(email_data: str):
    prompt = """
    You are an AI assistant that processes a day's worth of emails. 
    You must classify and summarize them into two groups:
    1. Urgent Emails (requiring immediate action).
    2. Digest Emails (summarized for an end-of-day digest).

    Rules:
    - Urgent Emails:
      - Criteria: deadlines within 24 hours, time-sensitive tasks, critical blockers, or explicitly marked urgent.
      - Include: sender, subject, summary (2–3 sentences), action_items, deadline.
    - Digest Emails:
      - Group into: priority (important but not urgent today), general_updates (informative, FYIs), low_priority (newsletters, promotions).
      - Each entry: sender, subject, summary (1–3 sentences), action_items (or "none").
    - End with digest_next_steps: consolidated list of action items from digest emails.
    - If a category has no emails, return [] (empty array).
    - Output must be valid JSON only. No other extra commentary. 

    JSON format:
    {
      "urgent_emails": [ { ... } ],
      "digest_emails": {
        "priority": [ { ... } ],
        "general_updates": [ { ... } ],
        "low_priority": [ { ... } ]
      },
      "digest_next_steps": [ ... ]
    }
    
    Email data to process:
    """ + email_data
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        output = response.text
        
        # Try to parse the output as JSON
        try:
            # Clean up the output in case there's extra text
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
