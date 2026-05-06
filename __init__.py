#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turkish Hyphenator — Calibre Interface Plugin
=============================================
Adds a toolbar button to Calibre. Click it to process the selected
Turkish EPUB(s) and fix justified text spacing.
"""

from calibre.customize import InterfaceActionBase


class TurkishHyphenatorPlugin(InterfaceActionBase):

    name                    = 'Turkish Hyphenator'
    description             = (
        'Inserts soft hyphens into selected Turkish EPUB(s) to fix '
        'ugly word-spacing in justified text (Apple Books, Kobo, etc.).'
    )
    supported_platforms     = ['windows', 'osx', 'linux']
    author                  = 'gba'
    version                 = (2, 0, 0)
    minimum_calibre_version = (5, 0, 0)

    #: Points Calibre to the actual GUI class
    actual_plugin = 'calibre_plugins.turkish_hyphenator.ui:TurkishHyphenatorAction'

    def is_customizable(self):
        return False
