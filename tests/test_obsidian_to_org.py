"""Tests for obsidian-to-org."""

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from obsidian_to_org.__main__ import convert_markdown_file, fix_markdown_comments


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

    Hello <!-- inline comment --> world.

    %%
    This is a block comment
    %%

    ---
    New hidden section.
    """)
    expected = dedent("""\
    * Title
    This is a paragraph.

    Hello world.

    #+begin_html
      <!--
      This is a block comment
      -->
    #+end_html

    --------------

    New hidden section.
    """)
    org = convert_file(markdown)
    assert org == expected


@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("foo", "foo"),
        ("before %%comment%% after", "before <!--comment--> after"),
        (
            """
            %%
            multiline
            %%
            """,
            """
            <!--
            multiline
            -->
            """,
         ),
    ]
)
def test_fix_markown_comments(input_text, expected):
    assert expected == fix_markdown_comments(input_text)

