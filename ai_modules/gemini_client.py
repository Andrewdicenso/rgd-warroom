from google import genai
from google.genai import types
import streamlit as st

def get_gemini_client():
    return genai.Client(api_key=st.secrets["google_api"]["gemini_api_key"])

def chiedi_a_gemini(prompt: str) -> str:
    client = get_gemini_client()
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return response.text
