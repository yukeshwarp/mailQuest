import streamlit as st
from config import client
from datetime import datetime, timedelta
from graph_util import fetch_emails, get_access_token
from relevance import get_relevant_mails
from preprocessor import preprocess_mail_details
import html2text

# Streamlit UI
st.set_page_config(page_title="mailQuest", layout="wide")
st.sidebar.title("Email Input")
user_email = st.sidebar.text_input("Enter User Email")

# Add a date picker for the user to select a start date
start_date = st.sidebar.date_input("Select a Start Date", min_value=datetime(2000, 1, 1).date(), max_value=datetime.today().date())

# Calculate 3 months from the start date
three_months_from_start = start_date + timedelta(days=90)

# If three_months_from_start is less than today, set max_value to today
max_date = min(three_months_from_start, datetime.today().date())

# Display the date range
st.sidebar.write("Mails on focus")
st.sidebar.write(f"From: {start_date} To: {max_date}")


if st.sidebar.button("Fetch Emails"):
    token = get_access_token()
    if token and user_email:
        # Fetch emails from the selected start date, limiting to 3 months from that date
        mails = fetch_emails(token, user_email, start_date, three_months_from_start)
        st.session_state["mails"] = mails
        st.sidebar.success(f"Fetched {len(mails)} emails")
    else:
        st.sidebar.error("Invalid email or authentication issue.")

# Chat Interface
st.title("mailQuest")
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about your emails"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    mails = st.session_state.get("mails", [])
    if mails:
        relevant_email_ids = get_relevant_mails(mails, prompt, start_date, three_months_from_start)
        relevant_mails = [mail for mail in mails if mail.get("id") in relevant_email_ids]

        if not relevant_mails:
            st.write("No relevant emails found.")

        h = html2text.HTML2Text()
        h.ignore_links = True

        # mail_details = "\n".join([ 
        #     f"Subject: {mail.get('subject', 'No Subject')}\n"
        #     f"From: {mail.get('from', {}).get('emailAddress', {}).get('address', 'Unknown Sender')}\n"
        #     f"Received: {mail.get('receivedDateTime', 'Unknown Time')}\n"
        #     f"Importance: {mail.get('importance', 'Normal')}\n"
        #     f"Read: {'Yes' if mail.get('isRead', False) else 'No'}\n"
        #     f"Body: {h.handle(mail.get('body', {}).get('content', 'No Content'))}"
        #     for mail in relevant_mails[:25]
        # ])

        preprocessed_mail_details = preprocess_mail_details(relevant_mails)

        with st.spinner("Thinking..."):
            # Use the OpenAI API to respond based on the emails
            response_stream = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "Answer the user's query based on the given emails."}, 
                          {"role": "user", "content": f"User's focus time period:- From:{start_date} To:{three_months_from_start} \n\nMails:\n{preprocessed_mail_details}\n\nUser's Query: {prompt}"}],
                temperature=0.5,
                stream=True,
            )
        
        bot_response = ""
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            for chunk in response_stream:
                if chunk.choices:
                    bot_response += chunk.choices[0].delta.content or ""
                    response_placeholder.markdown(bot_response)

        st.session_state["messages"].append({"role": "assistant", "content": bot_response})

