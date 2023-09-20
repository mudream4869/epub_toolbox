import streamlit as st

st.set_page_config(page_title='Novel TXT-EPUB Builder', page_icon='📘')

with open('README.md', encoding='utf-8') as fp:
    readme_cont = fp.read()
    # work-around for markdown image
    readme_cont.replace('![](txt2epub-preview.png)', '')
    st.markdown(readme_cont)
