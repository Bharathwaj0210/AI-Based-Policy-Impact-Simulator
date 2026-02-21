import streamlit as st
import requests

st.set_page_config(page_title="AI POLICY (NEW) Demo", layout="wide")

st.title("AI Policy Advisory & Impact Simulator")

st.sidebar.header("Navigation")
page = st.sidebar.selectbox("Choose a category", ["Insurance", "Government", "HR"])

if page == "Insurance":
    st.header("Insurance Policy Recommendation")
    # Streamlit UI for insurance
elif page == "Government":
    st.header("Government Eligibility Engine")
    # Streamlit UI for government
else:
    st.header("HR Policy Simulator")
    # Streamlit UI for HR
