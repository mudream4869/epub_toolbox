import io
import zipfile
from urllib.parse import urlparse

import requests
import streamlit as st

from ebooklib import epub


@st.cache_data(ttl='1d')
def get_image(uri: str):
    r = requests.get(uri, timeout=10)
    ret = io.BytesIO(r.content)
    ret.name = urlparse(uri).path.split('/')[-1]
    return ret


def write_epub(book: epub.EpubBook, buffer: io.BytesIO):
    ''' Write epub book to buffer'''
    writer = epub.EpubWriter('book.epub', book)
    writer.process()

    # Since writer.write only support writing to a file,
    # here we implement a function to write into a byte buffer
    writer.out = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)
    writer.out.writestr('mimetype', 'application/epub+zip',
                        compress_type=zipfile.ZIP_STORED)
    # pylint: disable=protected-access
    writer._write_container()
    writer._write_opf()
    writer._write_items()

    writer.out.close()
