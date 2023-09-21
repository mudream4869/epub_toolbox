import re
import io

from typing import List, Optional

import streamlit as st
import chardet

from ebooklib import epub

from util import write_epub, get_image


@st.cache_data(show_spinner='Detect coding...', ttl='1h')
def detect_coding(content: bytes):
    return chardet.detect_all(content[:500])


@st.cache_data(show_spinner='Decoding...', ttl='1h')
def decode_content(content: bytes, encoding: str) -> str:
    return content.decode(encoding, errors='ignore')


class Chapter:
    def __init__(self, title) -> None:
        self.title = title
        self.content_lines = []

    @property
    def html_content(self) -> str:
        return ''.join(
            f'<p>{line}</p>\n' for line in self.content_lines)

    def content(self, *, line_limit=0) -> str:
        if line_limit:
            return '\n'.join(self.content_lines[:line_limit])
        return '\n'.join(self.content_lines)


@st.cache_data(show_spinner='Splitting content to chapters...', ttl='1h')
def split_content(content_lines: List[str],
                  title_regs: List[str],
                  title_block_list: List[str]) -> List[Chapter]:
    regs = [re.compile(reg) for reg in title_regs]

    def is_title(line: str) -> bool:
        for block_line in title_block_list:
            if block_line in line:
                return False

        for allow_reg in regs:
            if allow_reg.match(line):
                return True

        return False

    chapters: List[Chapter] = [Chapter('Head (Content before first title)')]
    for line in content_lines:
        if is_title(line):
            chapters.append(Chapter(line))
            continue

        chapters[-1].content_lines.append(line)

    return chapters


def build_epub_book(book_title: str,
                    book_author: str,
                    book_intro: str,
                    book_cover: Optional[io.BytesIO],
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
        intro_file.content = ''.join(
            f'<p>{l}</p>' for l in book_intro.split('\n'))
        book.add_item(intro_file)
        book.toc.append(epub.Link(intro_filename, intro_title))
        spines.append(intro_file)

        book.add_metadata('DC', 'description', book_intro)

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
    st.set_page_config(page_title='Novel TXT-EPUB Builder', page_icon='📘')

    st.markdown('''
    # 📘 Novel TXT-EPUB Builder
    This tool assists in splitting a novel's plain text file
    into chapters and building an ePub file.
    ''')

    with st.expander('Steps', expanded=True):
        st.markdown('''
        1. Choose the TXT file containing the novel.
        2. Automatically split the TXT file into chapters using a regular expression
        based on chapter titles.
        3. Fill in the book's metadata.
        4. Click the `Prepare EPUB` button and wait for the Download button to appear.
        5. Download the generated ePub file.
        ''')

    txt_file = st.sidebar.file_uploader('Choose a txt file', ['txt'])
    if not txt_file:
        st.info('👈 Please select a text file to process')
        return

    content_bytes = txt_file.read()

    codes = detect_coding(content_bytes)

    code_option = ['select one'] + [res['encoding'] for res in codes]
    selected_encoding = st.sidebar.selectbox('Decode', code_option, index=0)
    if selected_encoding == 'select one':
        return

    content = decode_content(content_bytes, selected_encoding)
    content_lines = content.split('\n')

    remove_empty_lines = st.sidebar.checkbox('Remove empty lines')
    if remove_empty_lines:
        content_lines = [line for line in content_lines if line.strip()]

    st.sidebar.text(f'Codeset: {selected_encoding}')
    st.sidebar.text(f'Lines: {len(content_lines)}')
    st.sidebar.text(f'Char count: {len(content)}')

    tab_chapter, tab_chapter_preview, tab_meta = st.tabs(
        ['Chapters', 'Chapter Preview', 'Meta Data'])

    def make_list(xs: str) -> List[str]:
        return [x for x in xs.split('\n') if x]

    with tab_chapter:
        title_regs = make_list(st.text_area(
            label='Title allow list',
            value='第.*章.*',
            help=('Any line that match one of the regular expression here '
                  'considered as chapter titles.')))

        title_block_list = make_list(st.text_area(
            label='Title block list',
            help=('Any line that contain one of the line here '
                  'won\'t be a title')))

        if len(set(title_regs) & set(title_block_list)) > 0:
            st.warning('Block list and allow list has common line.')

        chapters = split_content(content_lines, title_regs, title_block_list)

        st.sidebar.text(f'Chapter counts: {len(chapters)}')

        default_intro = chapters[0].content(line_limit=500).strip()
        default_title: str = txt_file.name
        if default_title.endswith('.txt'):
            default_title = default_title[:-4]

        st.dataframe(
            {
                'Index': list(range(len(chapters))),
                'Titles':  [ch.title for ch in chapters],
                'Line counts': [len(ch.content_lines) for ch in chapters],
                'Content (first 500 lines)': [
                    ch.content(line_limit=500) for ch in chapters],
            },
            hide_index=True,
            use_container_width=True)

        if any(len(ch.content_lines) > 500 for ch in chapters):
            st.warning(
                'There are substantial chapters (> 500 lines) in existence; '
                'it\'s possible that your title regex is incorrect.')

    with tab_chapter_preview:
        sel_chapter_index = st.selectbox(
            'Choose preview chapter', range(len(chapters)),
            format_func=lambda x: chapters[x].title)

        if 0 <= sel_chapter_index < len(chapters):
            st.code(
                chapters[sel_chapter_index].content())

    with tab_meta:
        book_title = st.text_input('Title', value=default_title)
        book_author = st.text_input('Author')
        book_intro = st.text_area('Introduction', value=default_intro)
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
                book_intro.strip(), book_cover_file, chapters)

            with io.BytesIO() as buffer:
                write_epub(book, buffer)
                status.update(label='Preparing EPUB complete!',
                              state='complete', expanded=True)
                st.balloons()
                epub_filename = f'{book_title}.epub'
                st.download_button(f'Download {epub_filename}', data=buffer,
                                   file_name=epub_filename)


main()
