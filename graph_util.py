import msal
import requests
import logging as log
from config import *

# Set up logging
log.basicConfig(level=log.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_access_token():
    """Authenticate and get access token."""
    try:
        log.debug("Attempting to acquire an access token...")
        app = msal.ConfidentialClientApplication(
            CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
        )
        result = app.acquire_token_for_client(scopes=SCOPE)
        
        if "access_token" in result:
            log.info("Access token acquired successfully.")
            return result["access_token"]
        else:
            log.error(f"Failed to acquire access token: {result.get('error_description', 'Unknown error')}")
            return None

    except Exception as e:
        log.exception("Exception occurred while acquiring access token.")
        return None

def fetch_emails(access_token, user_email):
    """Fetch all emails from Outlook with metadata."""
    batch_size = 500
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages?$top={batch_size}"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    all_mails = []
    
    try:
        while url:
            log.debug(f"Fetching emails from URL: {url}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                all_mails.extend(data.get("value", []))
                
                # Check if there is a next page
                url = data.get("@odata.nextLink")
                if url:
                    log.debug(f"Next page found. Continuing to fetch emails.")
                else:
                    log.info("All emails fetched successfully.")
            else:
                log.error(f"Error fetching emails. Status code: {response.status_code}")
                log.error(f"Response: {response.text}")
                break
    
    except requests.exceptions.RequestException as req_err:
        log.exception("Request exception occurred while fetching emails.")
    except Exception as e:
        log.exception("An error occurred while fetching emails.")
    
    return all_mails
