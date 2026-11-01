import os

import requests
import streamlit as st


API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

API_CHAT_URL = f"{API_BASE_URL}/api/v1/chat"
API_PATIENTS_URL = f"{API_BASE_URL}/api/v1/patients"


st.set_page_config(
    page_title="Secure EHR Insight",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 Secure EHR Insight")

st.caption(
    "Patient-scoped clinical record retrieval "
    "with PHI redaction and AI safety controls."
)

st.warning(
    "This application is an educational prototype. "
    "It is not intended for diagnosis or treatment."
)


# -----------------------------
# Authentication
# -----------------------------

st.sidebar.header("Authentication")

access_token = st.sidebar.text_input(
    "Access token",
    type="password",
    key="access_token",
)

if not access_token:
    st.info("Enter your access token to continue.")
    st.stop()


headers = {
    "Authorization": f"Bearer {access_token}"
}


# -----------------------------
# Fetch authorized patients
# -----------------------------

try:

    response = requests.get(
        API_PATIENTS_URL,
        headers=headers,
        timeout=15,
    )

    response.raise_for_status()

    patient_list = response.json()["patients"]

except requests.exceptions.HTTPError as exc:

    if exc.response.status_code == 401:
        st.error("Authentication failed. Check your access token.")
    else:
        st.error("Unable to retrieve authorized patient records.")

    st.stop()

except requests.exceptions.RequestException:
    st.error("The API service is unavailable.")
    st.stop()


if not patient_list:
    st.info("No authorized patients with embedded records were found.")
    st.stop()


# -----------------------------
# Patient selection
# -----------------------------

patient_id = st.sidebar.selectbox(
    "Select authorized patient",
    patient_list,
)

# Reset history whenever patient selection changes.
if st.session_state.get("active_patient") != patient_id:

    st.session_state.active_patient = patient_id
    st.session_state.messages = []


if "messages" not in st.session_state:
    st.session_state.messages = []


st.sidebar.success("Patient access verified by the API.")


if st.sidebar.button("Clear conversation"):
    st.session_state.messages = []
    st.rerun()


# -----------------------------
# Chat history
# -----------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# -----------------------------
# Chat input
# -----------------------------

if prompt := st.chat_input("Ask about historical clinical records..."):

    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    payload = {
        "patient_id": patient_id,
        "messages": st.session_state.messages,
    }

    with st.chat_message("assistant"):

        with st.spinner("Retrieving clinical records..."):

            try:

                response = requests.post(
                    API_CHAT_URL,
                    headers=headers,
                    json=payload,
                    timeout=120,
                )

                response.raise_for_status()

                result = response.json()

                bot_reply = result["llm_response"]

                disclaimer = result.get(
                    "disclaimer",
                    "AI-generated retrieval summary.",
                )

                bot_reply += f"\n\n---\n*{disclaimer}*"

            except requests.exceptions.HTTPError as exc:

                status_code = exc.response.status_code

                if status_code == 401:
                    bot_reply = "Authentication failed. Please sign in again."

                elif status_code == 404:
                    bot_reply = "Patient access could not be verified."

                else:
                    bot_reply = "The clinical request could not be processed."

            except requests.exceptions.Timeout:
                bot_reply = "The request timed out. Please try again."

            except requests.exceptions.RequestException:
                bot_reply = "Unable to connect to the API service."

        st.markdown(bot_reply)

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply,
    })