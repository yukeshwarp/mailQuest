import time
import random
import concurrent.futures
from config import *

def get_relevant_mails(mails, query):
    relevant_mail_ids = []

    # Function to process a batch of mails
    def process_batch(batch):
        # Prepare mail details for the batch
        mail_details = ""
        for idx, mail in enumerate(batch):
            mail_detail = f"""
                    Mail {idx+1}:
                    Subject: {mail.get('subject', 'No Subject')}
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
            mail_details += mail_detail + "\n\n"
        
        prompt = f"""You are given with details of multiple mails and a user query. If any mail is relevant to respond to the user query, return "yes" for that mail's position in the batch (1 to 10), otherwise "no".
                    Mails details: {mail_details}
                    
                    User query: {query}
                    ---
                    Return a list of results (e.g., [1, 3, 5] for mails 1, 3, and 5 being relevant).
                    """
        
        # Retry logic with backoff and jitter
        max_retries = 5
        retries = 0

        while retries < max_retries:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "You are an intelligent email sorting assistant."},
                              {"role": "user", "content": prompt}],
                    temperature=0.3,
                )
                
                # Parse response and extract relevant mail positions
                relevant_positions = response.choices[0].message.content.strip()
                relevant_positions = [int(pos) - 1 for pos in relevant_positions.strip('[]').split(',') if pos.strip().isdigit()]
                
                # Extract the relevant mail IDs based on the positions
                return [batch[pos].get("id") for pos in relevant_positions]
            
            except openai.error.RateLimitError:  # Handle rate-limiting error specifically
                retries += 1
                backoff_time = (2 ** retries) + random.uniform(0, 1)  # Exponential backoff with jitter
                print(f"Rate limit hit, retrying in {backoff_time:.2f} seconds...")
                time.sleep(backoff_time)
            except Exception as e:
                print(f"Error processing batch: {e}")
                return []

        # If all retries fail, return an empty list
        print("Max retries reached. Skipping this batch.")
        return []

    # Batch the mails into groups of 10
    batches = [mails[i:i + 10] for i in range(0, len(mails), 10)]

    # Use ThreadPoolExecutor to process the batches concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map the batches to the process_batch function concurrently
        results = executor.map(process_batch, batches)

    # Collect relevant mail IDs from all batches
    for batch_result in results:
        relevant_mail_ids.extend(batch_result)

    return relevant_mail_ids
