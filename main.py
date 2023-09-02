import re
import io
import zipfile


from typing import BinaryIO, Tuple, List, Optional, Any

import streamlit as st
import chardet

from ebooklib import epub

st.title(':book: Novel TXT-EPUB Builder')


@st.cache_data(show_spinner=False)
def convert_encoding(uploaded_file: BinaryIO) -> Tuple[str, str]:
    body = uploaded_file.read()
    encoding_result = chardet.detect(body)
    content = body.decode(encoding_result['encoding'], errors='ignore')
    return content, encoding_result['encoding']


class Chapter:
    def __init__(self, title) -> None:
        self.title = title
        self.content_lines = []

    @property
    def html_content(self) -> str:
        return ''.join(
            f'<p>{line}</p>\n' for line in self.content_lines)


@st.cache_data(show_spinner=False)
def split_content(content_lines: List[str], reg_title: str) -> List[Chapter]:
    reg = re.compile(reg_title)

    chapters: List[Chapter] = [Chapter('Head (Content before first title)')]
    for line in content_lines:
        if reg.match(line):
            chapters.append(Chapter(line))
            continue

        chapters[-1].content_lines.append(line)

    return chapters


def build_epub_book(book_title: str,
                    book_author: str,
                    book_intro: str,
                    book_cover: Optional[Any],
                    chapters: List[Chapter]) -> epub.EpubBook:
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
        intro_file.content = book_intro
        book.add_item(intro_file)
        book.toc.append(epub.Link(intro_filename, intro_title))
        spines.append(intro_file)

    for index, chapter in enumerate(chapters[1:]):
        ch_filename = f'ch_{index}.html'
        ch_file = epub.EpubHtml(
            title=chapter.title, file_name=ch_filename)
        ch_file.content = f'<h1>{chapter.title}</h1>\n' + \
            chapter.html_content
        book.add_item(ch_file)

        book.toc.append(epub.Link(ch_filename, chapter.title))

        spines.append(ch_file)

    book.add_item(epub.EpubNav())

    # define CSS style
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style,
    )

    book.add_item(nav_css)

    # basic spine
    book.spine = ['nav'] + spines

    return book


def write_epub(book: epub.EpubBook, buffer: io.BytesIO):
    ''' Return bytes of epub book '''
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


def main():
    txt_file = st.sidebar.file_uploader('Choose txt file', ['txt'])
    if not txt_file:
        return

    with st.spinner('Convert coding...'):
        content, codeset = convert_encoding(txt_file)
        content_lines = content.split('\n')

    st.sidebar.text(f'Codeset: {codeset}')
    st.sidebar.text(f'Lines: {len(content_lines)}')

    tab_chapter, tab_meta = st.tabs(['Chapters', 'Meta'])

    reg_title = tab_chapter.text_input('Title regex', '第.*章.*')

    with st.spinner("Splitting content to chapters..."):
        chapters = split_content(content_lines, reg_title)

    default_intro = chapters[0].html_content
    default_title: str = txt_file.name
    if default_title.endswith('.txt'):
        default_title = default_title[:-4]

    tab_chapter.dataframe(
        {
            'Index': list(range(len(chapters))),
            'Titles':  [ch.title for ch in chapters],
            'Line counts': [len(ch.content_lines) for ch in chapters],
            'Content (first 1000 lines)': [
                '\n'.join(ch.content_lines[:1000]) for ch in chapters],
        },
        hide_index=True,
        use_container_width=True)

    book_title = tab_meta.text_input('Title', value=txt_file.name)
    book_author = tab_meta.text_input('Author')
    book_intro = tab_meta.text_area('Introduction', value=default_intro)
    book_cover = tab_meta.file_uploader('Book cover')

    if st.button('Prepare EPUB'):
        with st.status('Preparing EPUB...', expanded=True) as status:
            book = build_epub_book(
                book_title, book_author, book_intro, book_cover, chapters)

            with io.BytesIO() as buffer:
                write_epub(book, buffer)
                status.update(label='Preparing EPUB complete!',
                              state='complete', expanded=True)
                st.download_button('Download', data=buffer,
                                   file_name=book_title + '.epub')


main()
