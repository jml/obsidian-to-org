#!/usr/bin/python

import argparse
import os
import pathlib
import re
import sys
import tempfile


def make_arg_parser():
    parser = argparse.ArgumentParser(description="Convert an Obsidian Markdown file into org-mode")
    parser.add_argument("markdown_file", type=pathlib.Path, help="The Markdown file to convert")
    return parser


def prepare_markdown_text(markdown_contents):
    # Treat all comments in file
    obsidian_comment_re = re.compile(r"^%%(.*?)%%", re.MULTILINE)
    markdown_contents = obsidian_comment_re.sub(r"#!#comment: \1", markdown_contents)

    # Ensure space after "---"
    ruler_re = re.compile(r"^---\n(.+)", re.MULTILINE)
    return ruler_re.sub(r"---\n\n\1", markdown_contents)


def convert_markdown_file(md_file, output_dir):
    org_file = (output_dir / md_file.stem).with_suffix(".org")

    markdown_contents = prepare_markdown_text(md_file.read_text())

    # Convert from md to org
    with tempfile.NamedTemporaryFile("w+") as fp:
        fp.write(markdown_contents)
        fp.flush()
        pandoc_command = (
            f"pandoc -f markdown \"{fp.name}\" --lua-filter=remove-header-attr.lua --wrap=preserve -o {org_file}"
        )
        os.system(pandoc_command)

    org_contents = org_file.read_text()

    # Regularize comments
    org_comment_re = re.compile(r"^#!#comment:(.*?)$", re.MULTILINE)
    org_contents = org_comment_re.sub(r"#\1", org_contents)

    # Convert all kinds of links
    url_re = re.compile(r"\[\[(.*?)\]\[(.*?)\]\]")
    link_re = re.compile(r"\[\[(.*?)\]\]")
    link_description_re = re.compile(r"\[\[(.*?)\|(.*?)\]\]")

    new_content = ""
    matches = re.finditer(r"\[\[.*?\]\]", org_contents)
    pos = 0
    for m in matches:
        s = m.start()
        e = m.end()
        m_string = m.group(0)
        if "://" in m_string:
            new_content = (
                new_content + org_contents[pos:s] + re.sub(url_re, r"[[\1][\2]]", m_string)
            )
        elif "|" in m_string:
            new_content = (
                new_content
                + org_contents[pos:s]
                + re.sub(link_description_re, r"[[file:\1.org][\2]]", m_string)
            )
        else:
            new_content = (
                new_content
                + org_contents[pos:s]
                + re.sub(link_re, r"[[file:\1.org][\1]]", m_string)
            )

        pos = e
    new_content = new_content + org_contents[pos:]

    org_file.write_text(new_content)

    return org_file


def main():
    parser = make_arg_parser()
    args = parser.parse_args()

    output_dir = pathlib.Path("out")
    if not output_dir.is_dir():
        output_dir.mkdir()

    org_file = convert_markdown_file(md_file, output_dir)
    print(f"Converted {org_file}")


if __name__ == "__main__":
    main()
