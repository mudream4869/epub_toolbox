import io

from typing import List, Optional

from ebooklib import epub

import streamlit as st
import easyocr

from util import write_epub, get_image


@st.cache_resource(ttl='30d')
def ocr_reader(langs: List[str]) -> easyocr.Reader:
    return easyocr.Reader(langs, gpu=False, verbose=False)


@st.cache_data(ttl='1h')
def read_txt(img: io.BytesIO, langs: List[str]) -> List[str]:
    reader = ocr_reader(langs)
    return reader.readtext(img.read(), detail=0)


def build_epub_book(book_title: str,
                    book_author: str,
                    book_intro: str,
                    book_cover: Optional[io.BytesIO],
                    images: List[io.BytesIO]) -> epub.EpubBook:
    book = epub.EpubBook()
    book.set_title(book_title)
    if book_cover:
        book.set_cover(book_cover.name, book_cover.read())

    if book_author:
        book.add_author(book_author)

    book.toc = []
    spines = []

    if book_intro:
        intro_filename = 'intro.html'
        intro_title = 'Introduction'
        intro_file = epub.EpubHtml(
            title=intro_title, file_name=intro_filename)
        intro_file.content = ''.join(
            f'<p>{l}</p>' for l in book_intro.split('\n'))
        book.add_item(intro_file)
        book.toc.append(epub.Link(intro_filename, intro_title))
        spines.append(intro_file)

        book.add_metadata('DC', 'description', book_intro)

    cont_filename = 'content.html'
    cont_file = epub.EpubHtml(title='Content', file_name=cont_filename)
    cont = ''
    for index, image in enumerate(images):
        img_filename = 'img_%05d_%s' % (index, image.name)
        img_file = epub.EpubImage(file_name=img_filename, content=image.read())
        book.add_item(img_file)

        cont += '<div class="image-container">\n'
        cont += f'  <img src="{img_filename}" alt="Page {index + 1}">\n'
        cont += '</div>\n'

    cont_file.content = cont
    book.add_item(cont_file)
    book.toc.append(epub.Link(cont_filename, title=cont_filename))
    spines.append(cont_file)

    book.add_item(epub.EpubNav())

    # define CSS style
    style = '''
        body {
            color: white;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }
        .image-container {
            text-align: center;
            margin-bottom: 20px;
        }
        .image-container img {
            max-width: 100%;
            height: auto;
        }
    '''

    nav_css = epub.EpubItem(
        uid='style_nav',
        file_name='style/nav.css',
        media_type='text/css',
        content=style,
    )

    book.add_item(nav_css)

    # basic spine
    book.spine = ['nav'] + spines

    return book


def tab_images(images: List[io.BytesIO]):
    sel_img_index = st.selectbox('Filename', range(len(images)),
                                 format_func=lambda i: images[i].name)
    if 0 > sel_img_index or sel_img_index >= len(images):
        return

    sel_img = images[sel_img_index]

    with st.expander('OCR'):
        st.markdown('Using [EasyOCR](https://github.com/JaidedAI/EasyOCR)')
        langs = st.text_input('OCR Language, ex: ch_tra,en').split(',')
        if any(langs):
            ocr_result = read_txt(sel_img, langs)
            st.text('\n'.join(ocr_result))

    st.image(sel_img)


def main():
    st.set_page_config('Images-EPUB Builder', page_icon='🖼️')

    st.markdown('''
    # 🖼️ Images-EPUB Builder
    This tool packs images as an ePub file.
    ''')

    with st.expander('Steps', expanded=True):
        st.markdown('''
        1. Choose image files.
        2. Fill in the book's metadata
        3. Click the `Prepare EPUB` button and wait for the Download button to appear.
        4. Download the generated ePub file.
        ''')

    images = st.sidebar.file_uploader('Images', type=['png', 'jpg'],
                                      accept_multiple_files=True,
                                      key='images')
    if not images:
        return

    st.sidebar.text(f'Image Count: {len(images)}')

    tab_imgs, tab_meta = st.tabs(['Images Preview', 'Book Meta'])

    with tab_imgs:
        tab_images(images)

    with tab_meta:
        book_title = st.text_input('Title')
        book_author = st.text_input('Author')
        book_intro = st.text_area('Introduction')
        book_cover = st.file_uploader('Book cover')
        if not book_cover:
            book_cover_url = st.text_input('Book cover URL')

    if st.button('Prepare EPUB'):
        with st.status('Preparing EPUB...', expanded=True) as status:

            book_cover_file: Optional[io.BytesIO] = None
            if book_cover:
                book_cover_file = book_cover
            elif book_cover_url:
                book_cover_file = get_image(book_cover_url)

            book = build_epub_book(
                book_title.strip(), book_author.strip(),
                book_intro.strip(), book_cover_file, images)

            with io.BytesIO() as buffer:
                write_epub(book, buffer)
                status.update(label='Preparing EPUB complete!',
                              state='complete', expanded=True)
                st.balloons()
                epub_filename = f'{book_title}.epub'
                st.download_button(f'Download {epub_filename}', data=buffer,
                                   file_name=epub_filename)


main()
