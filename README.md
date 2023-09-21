# EPUB Toolbox

![](txt2epub-preview.png)

## Usage

### 📘 Novel TXT-EPUB Builder

This tool assists in splitting a novel's plain text file
into chapters and building an ePub file.

#### Steps

1. Choose the TXT file containing the novel.
2. Automatically split the TXT file into chapters using a regular expression
based on chapter titles.
3. Fill in the book's metadata.
4. Click the `Prepare EPUB` button and wait for the Download button to appear.
5. Download the generated ePub file.

### 🖼️ Images-EPUB Builder

Pack images as an ePub file.

#### Steps

1. Choose image files.
2. Fill in the book's metadata
3. Click the `Prepare EPUB` button and wait for the Download button to appear.
4. Download the generated ePub file.

## Run

```bash
python3 -m venv venv
python3 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\streamlit.exe run README.py
```

## Build

Currently, we only support windows executable.

```bash
python3 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements-release.txt
.\venv\Scripts\pyinstaller.exe app_entry.spec --clean
```
