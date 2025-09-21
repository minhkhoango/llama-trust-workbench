# app.py
import streamlit as st

st.set_page_config(
    page_title="LlaMaTrust Workbench",
    layout="wide"
)

st.title("LlamaTrust Workbench")
st.write("An interactive diagnostic tool for LlamaParse.")

st.info("Workbench is initializing... More featuers coming soon.", icon="⏳")

# Placeholder for the main two-column layout
col1, col2 = st.columns(2)

with col1:
    st.header("PDF Viewer")
    st.warning("PDF rendering will appear here.")

with col2:
    st.header("Parsing Trace")
    st.warning("Interactive trace output will appear here.")