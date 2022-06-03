#!/usr/bin/python

import argparse
import pathlib
import re
import subprocess
import sys
import tempfile


COMMENT_MARKER = "#!#comment:"

def make_arg_parser():
    parser = argparse.ArgumentParser(description="Convert an Obsidian Markdown file into org-mode")
    parser.add_argument("markdown_file", type=pathlib.Path, help="The Markdown file to convert")
    return parser


def fix_markdown_comments(markdown_contents):
    """Turn Obsidian comments into HTML comments."""
    chunks = markdown_contents.split("%%")
    inside_comment = False
    output = []
    for i, chunk in enumerate(chunks):
        if not inside_comment:
            output.append(chunk)
            inside_comment = True
        else:
            if "\n" in chunk:
                lines = chunk.splitlines(True)
                if len(lines) > 0 and lines[0].strip() == "":
                    lines = lines[1:]
                output.extend(f"{COMMENT_MARKER}{line}" for line in lines)
            else:
                output.extend(["<!--", chunk, "-->"])
            inside_comment = False
    return "".join(output)


def restore_comments(org_contents):
    """Restore the comments in org format."""
    return "".join(line.replace(COMMENT_MARKER, "# ") for line in  org_contents.splitlines(True))


def prepare_markdown_text(markdown_contents):
    markdown_contents = fix_markdown_comments(markdown_contents)

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
        subprocess.run(
            [
                "pandoc",
                "--from=markdown-auto_identifiers",
                "--to=org",
                "--wrap=preserve",
                "--output",
                org_file,
                fp.name,
            ],
            check=True,
        )

    org_contents = org_file.read_text()

    org_contents = restore_comments(org_contents)

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
