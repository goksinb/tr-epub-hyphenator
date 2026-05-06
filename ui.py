#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui.py — Calibre GUI action for Turkish Hyphenator.
Adds a toolbar button; clicking it processes the selected books.
"""

from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog, question_dialog


class TurkishHyphenatorAction(InterfaceAction):

    name = 'Turkish Hyphenator'
    # (text, icon_name, tooltip, keyboard_shortcut)
    action_spec = (
        'Turkish Hyphenator',
        'languages.png',
        'Fix justified text spacing in selected Turkish EPUB(s)',
        None,
    )

    def genesis(self):
        """Called once when the plugin is initialised."""
        self.qaction.triggered.connect(self.run)

    def run(self):
        """Called when the toolbar button is clicked."""
        from calibre_plugins.turkish_hyphenator.hyphenator import fix_epub
        import os, tempfile, shutil

        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            error_dialog(
                self.gui,
                'No books selected',
                'Please select one or more EPUB books in your library first.',
                show=True,
            )
            return

        db = self.gui.current_db.new_api
        ids = [self.gui.library_view.model().id(r) for r in rows]

        # Filter to EPUBs only
        epub_ids = []
        for book_id in ids:
            fmts = db.formats(book_id)
            if fmts and 'EPUB' in [f.upper() for f in fmts]:
                epub_ids.append(book_id)

        if not epub_ids:
            error_dialog(
                self.gui,
                'No EPUBs found',
                'None of the selected books have an EPUB format. '
                'Please select books that have an EPUB version.',
                show=True,
            )
            return

        # Confirm
        count = len(epub_ids)
        if not question_dialog(
            self.gui,
            'Turkish Hyphenator',
            f'Process {count} EPUB book{"s" if count > 1 else ""} '
            f'for Turkish hyphenation?\n\n'
            f'The EPUB file(s) in your library will be updated in place.',
        ):
            return

        processed = 0
        errors = []

        for book_id in epub_ids:
            title = db.field_for('title', book_id) or f'Book {book_id}'
            try:
                # Get the path to the EPUB
                epub_path = db.format_abspath(book_id, 'EPUB')
                if not epub_path or not os.path.exists(epub_path):
                    errors.append(f'{title}: EPUB file not found on disk.')
                    continue

                # Process to a temp file then replace
                with tempfile.NamedTemporaryFile(
                    suffix='.epub', delete=False
                ) as tmp:
                    tmp_path = tmp.name

                fix_epub(epub_path, tmp_path)
                shutil.move(tmp_path, epub_path)
                processed += 1

            except Exception as e:
                errors.append(f'{title}: {e}')
                if 'tmp_path' in dir() and os.path.exists(tmp_path):
                    os.remove(tmp_path)

        # Report results
        msg = f'Successfully processed {processed} book{"s" if processed != 1 else ""}.'
        if errors:
            msg += '\n\nErrors:\n' + '\n'.join(f'• {e}' for e in errors)

        info_dialog(
            self.gui,
            'Turkish Hyphenator — Done',
            msg,
            show=True,
        )

        # Refresh library view
        self.gui.library_view.model().refresh()
        # tags_browser was renamed in newer Calibre versions
        tb = getattr(self.gui, 'tags_browser', None) or getattr(self.gui, 'tag_browser', None)
        if tb is not None:
            tb.recount()
