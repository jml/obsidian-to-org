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


def main():
    parser = make_arg_parser()
    args = parser.parse_args()

    if not os.path.isdir("out/"):
        os.mkdir("out/")

    md_file = str(args.markdown_file)
    org_file = md_file[:-3] + ".org"

    # Treat all comments in file
    re_comm = re.compile(r"^%%(.*?)%%", re.MULTILINE)
    replace(re_comm, r"#!#comment: \1", md_file)

    # Ensure space after "---"
    re_ruler = re.compile(r"^---\n(.+)", re.MULTILINE)
    replace(re_ruler, r"---\n\n\1", md_file)

    # Convert from md to org
    pandoc_command = (
        'pandoc -f markdown "{0}" --lua-filter=remove-header-attr.lua'
        ' --wrap=preserve -o out/"{1}"'.format(md_file, org_file)
    )
    os.system(pandoc_command)

    # Regularize comments
    re_comm_org = re.compile(r"^#!#comment:(.*?)$", re.MULTILINE)
    replace(re_comm_org, r"#\1", "out/" + org_file)

    # Convert all kinds of links
    re_url = re.compile(r"\[\[(.*?)\]\[(.*?)\]\]")
    re_link = re.compile(r"\[\[(.*?)\]\]")
    re_link_description = re.compile(r"\[\[(.*?)\|(.*?)\]\]")

    with open("out/" + org_file, "r+") as f:
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
                    new_content + content[pos:s] + re.sub(re_url, r"[[\1][\2]]", m_string)
                )
            elif "|" in m_string:
                new_content = (
                    new_content
                    + content[pos:s]
                    + re.sub(re_link_description, r"[[file:\1.org][\2]]", m_string)
                )
            else:
                new_content = (
                    new_content
                    + content[pos:s]
                    + re.sub(re_link, r"[[file:\1.org][\1]]", m_string)
                )

            pos = e
        new_content = new_content + content[pos:]
        f.seek(0)
        f.write(new_content)
        f.truncate()

    print("Converted " + org_file)


if __name__ == "__main__":
    main()
