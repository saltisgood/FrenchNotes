from .parser.extensions import BlueElem
from .parser.html_renderer import HtmlRendererMixin

import marko

from argparse import ArgumentParser
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from shutil import rmtree
from typing import Callable, Protocol


class FileType(StrEnum):
    Csv = ".csv"
    Markdown = ".md"


@dataclass(frozen=True)
class File:
    path: Path
    type: FileType


class Generator(Protocol):
    @property
    def suffix(self) -> str:
        ...

    def generate_from_csv(self, text: str) -> str:
        ...
    
    def generate_from_md(self, text: str) -> str:
        ...


class AnkiGenerator:
    @property
    def suffix(self):
        return ".txt"

    def generate_from_csv(self, csv_text: str):
        csv_lines = csv_text.splitlines()
        header = csv_lines[0]
        columns = header.split(';')
        if len(columns) <= 1:
            raise RuntimeError(f"Columns were not split by ';': {header}")
        
        dest_lines = [
            "#separator:Semicolon",
            f"#columns:{header}",
        ]
        dest_lines.extend(csv_lines[1:])

        return "\n".join(dest_lines)

    def generate_from_md(self, md_text: str):
        md_lines = md_text.splitlines()
        header = md_lines[0]
        if not header.startswith("# "):
            raise RuntimeError(f"Unexpected header: {header}")

        md = marko.Markdown()
        doc = md.parse("\n".join(md_lines[1:]))
        html_content = md.render(doc)
        
        dest_lines = [
            "#separator:Semicolon",
            "#columns:Title;Content",
            html_content.replace("\n", "")
        ]

        return "\n".join(dest_lines)


class MarkdownGenerator:
    @property
    def suffix(self):
        return ".md"
    
    def generate_from_csv(self, csv_text: str):
        return "Not implemented"
    
    def generate_from_md(self, md_text: str):
        return md_text


def _find_src_files(root: Path):
    if not root.is_dir():
        raise RuntimeError(f"{root} is not a directory")
    
    src_files: list[File] = []

    for f in root.iterdir():
        if f.is_dir():
            src_files.extend(_find_src_files(f))
        elif f.is_file():
            file_type = FileType(f.suffix)
            src_files.append(File(f, file_type))
    
    return src_files


def _generate_files(src_files: list[File], src_dir: Path, dest_dir: Path, generator: Generator):
    for src_file in src_files:
        rel_src_path = src_file.path.relative_to(src_dir)
        dest_path = dest_dir.joinpath(rel_src_path).with_suffix(generator.suffix)
        try:
            if src_file.type == FileType.Csv:
                dest_text = generator.generate_from_csv(src_file.path.read_text())
            elif src_file.type == FileType.Markdown:
                dest_text = generator.generate_from_md(src_file.path.read_text())
            else:
                raise NotImplementedError(f"Unknown src file type: {src_file}")
        except RuntimeError as e:
            print(f"Error generating from {src_file.path}: {e}")
        else:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(dest_text)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--root", default=".", help="The root directory to use")
    parser.add_argument("--clear", action="store_true", help="Clear the destination directories before writing")
    args = parser.parse_args()

    root = Path(args.root)
    src_dir = root / "src"
    anki_dir = root / "anki"
    md_dir = root / "md"

    if args.clear:
        if anki_dir.exists():
            rmtree(anki_dir, ignore_errors=True)
        if md_dir.exists():
            rmtree(md_dir, ignore_errors=True)

    src_files = _find_src_files(src_dir)
    _generate_files(src_files, src_dir, root / "anki", AnkiGenerator())
    _generate_files(src_files, src_dir, root / "md", MarkdownGenerator())

# def _main(file: str, print_only: bool):
#     with open(file, encoding="UTF-8") as f:
#         raw_md = f.read()
    
#     extended_html = marko.MarkoExtension(
#         elements=[BlueElem],
#         renderer_mixins=[HtmlRendererMixin],
#     )
    
#     markdown = marko.Markdown(extensions=[extended_html])
#     doc = markdown.parse(raw_md)
#     print(markdown.render(doc))
    
    # doc = marko.parse(raw_md)
    # print(marko.render(doc))