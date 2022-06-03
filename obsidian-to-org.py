#!/usr/bin/python

import argparse
import os
import pathlib
import re
import sys


def replace(pattern, substitution, filename):
    f = open(filename, "r+")
    content = f.read()
    content = re.sub(pattern, substitution, content)
    f.seek(0)
    f.write(content)
    f.truncate()
    f.close()


def make_arg_parser():
    parser = argparse.ArgumentParser(description="Convert an Obsidian Markdown file into org-mode")
    parser.add_argument("markdown_file", type=pathlib.Path, help="The Markdown file to convert")
    return parser


def convert_markdown_file(md_file, output_dir):
    org_file = (output_dir / md_file.stem).with_suffix(".org")

    # Treat all comments in file
    obsidian_comment_re = re.compile(r"^%%(.*?)%%", re.MULTILINE)
    replace(obsidian_comment_re, r"#!#comment: \1", md_file)

    # Ensure space after "---"
    ruler_re = re.compile(r"^---\n(.+)", re.MULTILINE)
    replace(ruler_re, r"---\n\n\1", md_file)

    # Convert from md to org
    pandoc_command = (
        f"pandoc -f markdown \"{md_file}\" --lua-filter=remove-header-attr.lua --wrap=preserve -o {org_file}"
    )
    os.system(pandoc_command)

    # Regularize comments
    org_comment_re = re.compile(r"^#!#comment:(.*?)$", re.MULTILINE)
    replace(org_comment_re, r"#\1", org_file)

    # Convert all kinds of links
    url_re = re.compile(r"\[\[(.*?)\]\[(.*?)\]\]")
    link_re = re.compile(r"\[\[(.*?)\]\]")
    link_description_re = re.compile(r"\[\[(.*?)\|(.*?)\]\]")

    with open(org_file, "r+") as f:
        content = f.read()
        new_content = ""
        matches = re.finditer(r"\[\[.*?\]\]", content)
        pos = 0
        for m in matches:
            s = m.start()
            e = m.end()
            m_string = m.group(0)
            if "://" in m_string:
                new_content = (
                    new_content + content[pos:s] + re.sub(url_re, r"[[\1][\2]]", m_string)
                )
            elif "|" in m_string:
                new_content = (
                    new_content
                    + content[pos:s]
                    + re.sub(link_description_re, r"[[file:\1.org][\2]]", m_string)
                )
            else:
                new_content = (
                    new_content
                    + content[pos:s]
                    + re.sub(link_re, r"[[file:\1.org][\1]]", m_string)
                )

            pos = e
        new_content = new_content + content[pos:]
        f.seek(0)
        f.write(new_content)
        f.truncate()

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
