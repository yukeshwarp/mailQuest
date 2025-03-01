import streamlit as st
import requests
import os
from openai import AzureOpenAI
import html2text
import json
import re
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import Normalizer
from sklearn.decomposition import NMF
from graph_util import fetch_emails, get_access_token
from relevance import get_relevant_mails
from config import *

mails = ""
# Streamlit UI
st.set_page_config(page_title="mailQuest", layout="wide")
st.sidebar.title("Email Input")
user_email = st.sidebar.text_input("Enter User Email")

if st.sidebar.button("Fetch Emails"):
    token = get_access_token()
    if token and user_email:
        mails = fetch_emails(token, user_email)
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
        relevant_email_ids = get_relevant_mails(mails, prompt)
        relevant_mails = [mail for mail in mails if mail.get("id") in relevant_email_ids]

        if not relevant_mails:
            st.write("No relevant emails found.")

        h = html2text.HTML2Text()
        h.ignore_links = True

        mail_details = "\n".join([
            f"Subject: {mail.get('subject', 'No Subject')}\n"
            f"From: {mail.get('from', {}).get('emailAddress', {}).get('address', 'Unknown Sender')}\n"
            f"Received: {mail.get('receivedDateTime', 'Unknown Time')}\n"
            f"Body: {h.handle(mail.get('body', {}).get('content', 'No Content'))}"
            for mail in relevant_mails[:25]
        ])

        with st.spinner("Thinking..."):
            response_stream = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "Answer the user's query based on the given emails."}, {"role": "user", "content": mail_details + f"\n\nUser's Query: {prompt}"}],
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
