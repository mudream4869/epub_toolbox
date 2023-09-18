import io

from typing import List, Optional

from ebooklib import epub

import streamlit as st

from util import write_epub, get_image


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

    for index, image in enumerate(images):
        img_filename = 'img_%05d_%s' % (index, image.name)
        img_file = epub.EpubImage(file_name=img_filename, content=image.read())
        book.add_item(img_file)

        ch_filename = f'ch_{index}.html'
        ch_file = epub.EpubHtml(
            title=img_filename, file_name=ch_filename)
        ch_file.content = f'<img src="{img_filename}" class="max-size-img">\n'
        book.add_item(ch_file)

        book.toc.append(epub.Link(ch_filename, title=img_filename))

        spines.append(ch_file)

    book.add_item(epub.EpubNav())

    # define CSS style
    style = '''
        BODY {color: white;}
        .max-size-img {
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


def main():
    st.set_page_config('Images-EPUB Builder', page_icon='🖼️')
    images = st.sidebar.file_uploader('Images', type=['png', 'jpg'],
                                      accept_multiple_files=True,
                                      key='images')
    if not images:
        return

    st.sidebar.text(f'Image Count: {len(images)}')

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
