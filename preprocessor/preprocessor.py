import nltk
from nltk.corpus import stopwords
import re
import string

# Download the stopwords if not already downloaded
nltk.download('stopwords')

# Preprocessing function to remove stopwords and perform other text cleaning
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()

    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)

    # Tokenize text into words
    words = text.split()

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word not in stop_words]

    # Join words back into a string
    return ' '.join(filtered_words)

# Preprocess the mail details
def preprocess_mail_details(mails):
    h = html2text.HTML2Text()
    h.ignore_links = True

    # Combine mail details and preprocess
    preprocessed_details = "\n".join([ 
        f"Subject: {preprocess_text(mail.get('subject', 'No Subject'))}\n"
        f"From: {preprocess_text(mail.get('from', {}).get('emailAddress', {}).get('address', 'Unknown Sender'))}\n"
        f"Received: {preprocess_text(mail.get('receivedDateTime', 'Unknown Time'))}\n"
        f"Importance: {preprocess_text(mail.get('importance', 'Normal'))}\n"
        f"Read: {'Yes' if mail.get('isRead', False) else 'No'}\n"
        f"Body: {preprocess_text(h.handle(mail.get('body', {}).get('content', 'No Content')))}"
        for mail in mails[:25]
    ])
    
    return preprocessed_details

# Example usage:
preprocessed_mail_details = preprocess_mail_details(relevant_mails)
