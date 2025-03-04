import concurrent.futures
from config import *

def get_relevant_mails(mails, query):
    relevant_mail_ids = []

    # Function to process each individual mail and interact with the API
    def process_mail(mail):
        detail = f"""Subject: {mail.get('subject', 'No Subject')}
                    From: {mail.get('from', {}).get('emailAddress', {}).get('address', 'Unknown Sender')}
                    Received: {mail.get('receivedDateTime', 'Unknown Time')}
                    Importance: {mail.get('importance', 'Normal')}
                    Read: {'Yes' if mail.get('isRead', False) else 'No'}
                    Has Attachment: {mail.get('hasAttachments', False)}
                    Categories: {', '.join(mail.get('categories', [])) if mail.get('categories') else 'None'}
                    Conversation ID: {mail.get('conversationId', 'N/A')}
                    Weblink: {mail.get('webLink', 'No Link')}
                    Body Preview: {mail.get('bodyPreview', 'No Preview')}
                """

        prompt = f"""You are given with the details of a mail and user query. If the mail is relevant to respond to user query return "yes", if not return "no".
                    Mail details: {detail}
                    
                    User query: {query}
                    ---
                    Return "yes" or "no" with no additional words strictly.
                    """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an intelligent email sorting assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        if response.choices[0].message.content.strip().lower() == "yes":
            return mail.get("id")
        return None

    # Use ThreadPoolExecutor to process the mails concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map the mails to the process_mail function concurrently
        results = executor.map(process_mail, mails)

    # Collect relevant mail IDs
    relevant_mail_ids = [result for result in results if result is not None]

    return relevant_mail_ids
