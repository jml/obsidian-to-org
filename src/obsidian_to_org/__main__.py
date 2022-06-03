#!/usr/bin/python

import argparse
import pathlib
import re
import subprocess
import sys
import tempfile
import uuid


COMMENT_MARKER = "#!#comment:"
RULER_RE = re.compile(r"^---\n(.+)", re.MULTILINE)
LINK_RE = re.compile(r"\[\[([^|\[]*?)\]\]")
LINK_DESCRIPTION_RE = re.compile(r"\[\[(.*?)\|(.*?)\]\]")

# For example, [[file:foo.org][The Title is Foo]]
FILE_LINK_RE = re.compile(r"\[\[file:(.*?)\]\[(.*?)\]\]")


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
    return RULER_RE.sub(r"---\n\n\1", markdown_contents)


def fix_links(org_contents):
    """Convert all kinds of links."""
    org_contents = LINK_RE.sub(r"[[file:\1.org][\1]]", org_contents)
    org_contents = LINK_DESCRIPTION_RE.sub(r"[[file:\1.org][\2]]", org_contents)
    return org_contents


def convert_file_links_to_id_links(org_contents, nodes):
    def replace_with_id(match):
        node_id = nodes.get(match.group(1))
        if not node_id:
            return match.group(0)
        return f"[[id:{node_id}][{match.group(2)}]]"

    return FILE_LINK_RE.sub(replace_with_id, org_contents)


def convert_markdown_file(md_file, org_file):
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
    org_contents = fix_links(org_contents)
    org_file.write_text(org_contents)


def walk_directory(path):
    # From https://stackoverflow.com/questions/6639394/what-is-the-python-way-to-walk-a-directory-tree
    for p in path.iterdir():
        if p.is_dir():
            yield from walk_directory(p)
            continue
        yield p.resolve()


def single_file():
    parser = argparse.ArgumentParser(description="Convert an Obsidian Markdown file into org-mode")
    parser.add_argument("markdown_file", type=pathlib.Path, help="The Markdown file to convert")
    args = parser.parse_args()

    # TODO: Make this an argument.
    output_dir = pathlib.Path("out")
    if not output_dir.is_dir():
        output_dir.mkdir()

    org_file = (output_dir / md_file.stem).with_suffix(".org")
    convert_markdown_file(md_file, org_file)
    print(f"Converted {md_file} to {org_file}")


def add_node_id(org_file, node_id):
    contents = org_file.read_text()
    with org_file.open("w") as fp:
        fp.write(":PROPERTIES\n")
        fp.write(f":ID: {node_id}\n")
        fp.write(":END\n")
        fp.write(f"+title: {org_file.stem}\n\n")
        fp.write(contents)


def convert_directory():
    parser = argparse.ArgumentParser(description="Convert a directory of Obsidian markdown files into org-mode")
    parser.add_argument("markdown_directory", type=pathlib.Path, help="The directory of Markdown files to convert")
    parser.add_argument("output_directory", type=pathlib.Path, help="The directory to put the org files in")
    args = parser.parse_args()

    markdown_directory = args.markdown_directory.resolve()

    if not args.output_directory.is_dir():
        args.output_directory.mkdir()

    nodes = {}

    for path in walk_directory(markdown_directory):
        if path.suffix != ".md":
            continue
        org_filename = path.relative_to(markdown_directory).with_suffix(".org")
        org_path = args.output_directory / org_filename
        org_path.parent.mkdir(parents=True, exist_ok=True)
        convert_markdown_file(path, org_path)
        nodes[str(org_filename)] = node_id = str(uuid.uuid4()).upper()
        add_node_id(org_path, node_id)
        print(f"Converted {path} to {org_filename}")

    for org_path in walk_directory(args.output_directory):
        contents = org_path.read_text()
        org_path.write_text(convert_file_links_to_id_links(contents, nodes))
        print(f"Converted links in {org_path}")

    # TODO: What about tags (e.g. #literature). See https://www.orgroam.com/manual.html#Tags


if __name__ == "__main__":
    main()
