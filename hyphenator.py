#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hyphenator.py — Core Turkish hyphenation logic for the Calibre plugin.
Shared by ui.py so the GUI stays clean and the algorithm is easy to update.
"""

import re
import os
import zipfile
import tempfile

VOWELS = set('aeıioöuüAEIİOÖUÜ')
SHY = '\u00ad'  # soft hyphen (U+00AD)

HYPHEN_CSS = """
/* ---- Turkish Hyphenator v2 ---- */
body, p {
    -webkit-hyphens: auto;
    -epub-hyphens: auto;
    hyphens: auto;
    -webkit-hyphenate-limit-before: 2;
    -webkit-hyphenate-limit-after: 2;
    hyphenate-limit-chars: 4 2 2;
    adobe-hyphenate: auto;
    word-spacing: -0.03em;
    text-justify: inter-word;
}
h1, h2, h3, h4, h5, h6 {
    -webkit-hyphens: none;
    -epub-hyphens: none;
    hyphens: none;
    word-spacing: normal;
}
"""


def turkish_syllabify(word):
    """
    Insert soft hyphens into a Turkish word using vowel-position analysis.

    Rules:
    - 0 consonants between vowels  → break between them
    - 1 consonant between vowels   → consonant goes with next syllable
    - 2 consonants between vowels  → first stays, second goes next
    - 3+ consonants between vowels → all but last stay, last goes next

    Min word length: 4. Min chars on each side of break: 2.
    """
    if len(word) < 4:
        return word
    if not re.match(r'^[a-zA-ZğüşıöçĞÜŞİÖÇ]+$', word):
        return word

    vowel_positions = [i for i, c in enumerate(word) if c in VOWELS]
    if len(vowel_positions) <= 1:
        return word

    boundaries = []
    for k in range(len(vowel_positions) - 1):
        v1 = vowel_positions[k]
        v2 = vowel_positions[k + 1]
        cons = v2 - v1 - 1
        if cons == 0:
            boundaries.append(v1 + 1)
        elif cons == 1:
            boundaries.append(v1 + 1)
        elif cons == 2:
            boundaries.append(v1 + 2)
        else:
            boundaries.append(v2 - 1)

    result = list(word)
    for b in reversed(boundaries):
        if b >= 2 and (len(word) - b) >= 2:
            result.insert(b, SHY)
    return ''.join(result)


def hyphenate_text(text):
    """Apply Turkish syllabification to every word in a plain text string."""
    parts = re.split(r'(\W+)', text)
    return ''.join(
        turkish_syllabify(p) if re.match(r'^\w', p) else p
        for p in parts
    )


def process_xhtml(content):
    """
    Insert soft hyphens into text nodes of an XHTML/HTML string.
    Skips <head> content and tag attribute text.
    """
    parts = re.split(r'(<[^>]+>)', content)
    result = []
    in_head = False
    for part in parts:
        if part.startswith('<'):
            tag_lower = part.lower()
            if '<head' in tag_lower:
                in_head = True
            elif '</head' in tag_lower:
                in_head = False
            result.append(part)
        else:
            result.append(part if in_head else hyphenate_text(part))
    return ''.join(result)


def fix_epub(input_path, output_path):
    """
    Process an EPUB: insert soft hyphens into all XHTML content,
    patch CSS for hyphenation hints, and set lang="tr" on HTML elements.
    """
    with tempfile.TemporaryDirectory() as tmpdir:

        with zipfile.ZipFile(input_path, 'r') as z:
            z.extractall(tmpdir)

        for root, dirs, files in os.walk(tmpdir):
            for filename in files:
                filepath = os.path.join(root, filename)
                ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''

                if ext in ('xhtml', 'html', 'htm'):
                    with open(filepath, 'r', encoding='utf-8',
                              errors='replace') as f:
                        content = f.read()

                    if 'lang=' not in content[:500]:
                        content = re.sub(
                            r'(<html\b)([^>]*>)',
                            r'\1 xml:lang="tr" lang="tr"\2',
                            content, count=1
                        )
                    content = process_xhtml(content)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)

                elif ext == 'css':
                    with open(filepath, 'r', encoding='utf-8',
                              errors='replace') as f:
                        css = f.read()

                    css = css.replace('text-align: align-left', 'text-align: left')
                    css = css.replace('text-align: align-right', 'text-align: justify')
                    css = re.sub(
                        r'/\* ---- Turkish Hyphenator.*?\*/',
                        '', css, flags=re.DOTALL
                    )
                    css += HYPHEN_CSS

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(css)

        # Repack — mimetype must be first and uncompressed (EPUB spec)
        with zipfile.ZipFile(output_path, 'w') as zout:
            mimetype_path = os.path.join(tmpdir, 'mimetype')
            if os.path.exists(mimetype_path):
                zout.write(mimetype_path, 'mimetype',
                           compress_type=zipfile.ZIP_STORED)

            for dirpath, dirnames, filenames in os.walk(tmpdir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    arcname = os.path.relpath(filepath, tmpdir)
                    if arcname == 'mimetype':
                        continue
                    zout.write(filepath, arcname,
                               compress_type=zipfile.ZIP_DEFLATED)
