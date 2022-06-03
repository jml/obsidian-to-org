"""Tests for obsidian-to-org."""

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from obsidian_to_org.__main__ import convert_markdown_file


def convert_file(markdown_contents):
    """Wrapper function to convert markdown text to org text."""
    with tempfile.NamedTemporaryFile("w+") as markdown_file:
        markdown_file.write(markdown_contents)
        markdown_file.flush()

        with tempfile.TemporaryDirectory() as output_dir:
            org_file = convert_markdown_file(Path(markdown_file.name), Path(output_dir))
            return org_file.read_text()


def test_convert_markdown_file():
    markdown = dedent("""
    # Title

    This is a paragraph.

    %%
    This is a comment
    %%

    ---
    New hidden section.
    """)
    expected = dedent("""\
    * Title
    This is a paragraph.

    %%
    This is a comment
    %%

    --------------

    New hidden section.
    """)
    org = convert_file(markdown)
    assert org == expected
