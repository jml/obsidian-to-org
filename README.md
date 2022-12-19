# obsidian-to-org

Convert Obsidian files to org-roam

Based on @rberaldo's [pioneering work](https://gist.github.com/rberaldo/2a3bd82d5ed4bc39fee7e8ff4a6242b2).

See also

https://org-roam.discourse.group/t/fully-migrating-from-obsidian/1708

https://emacs-china.org/t/obsidian-to-org-python/23125

## Use without install as python package

```shell
cd obsidian-to-org/src/obsidian-to-org/
python3 __main__.py [obsidian dir] [output dir]
```

## Install as python package

Install requirements/dependencies

```shell
cd obsidian-to-org/
poetry install
```

(Optional) Build obsidian-to-org if dist/ doesn't exists

```shell
poetry build
```

Install obsidian-to-org

```
cd dist/
pip3 install obsidian_to_org-0.1.0-py3-none-any.whl
```

### Help

```shell
$ obsidian-to-org --help
usage: obsidian-to-org [-h] markdown_file

Convert an Obsidian Markdown file into org-mode

positional arguments:
  markdown_file  The Markdown file to convert

options:
  -h, --help     show this help message and exit
```

## Misc


