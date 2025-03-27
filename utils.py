import streamlit as st

def style_buttons():
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(to bottom, rgba(175,202,184, 1), rgba(113,150,125,1));
        }
    </style>
    """, unsafe_allow_html=True)