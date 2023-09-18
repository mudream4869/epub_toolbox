import streamlit as st

st.set_page_config(page_title='Novel TXT-EPUB Builder', page_icon='📘')

with open('README.md', encoding='utf-8') as fp:
    st.markdown(fp.read())
