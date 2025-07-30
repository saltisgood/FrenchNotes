from argparse import ArgumentParser
from dataclasses import dataclass, fields
from enum import StrEnum
from pathlib import Path
from shutil import rmtree
from typing import Iterable, Protocol, Sequence, TypeVar

import marko


class FileType(StrEnum):
    Grammar = "Grammar"
    Vocab = "Vocab"
    AdjectivePreposition = "AdjectivePreposition"
    VerbPreposition = "VerbPreposition"


class ParsedFileType:
    FIELDS: Sequence[str]
    NOTE_TYPE: str
    DECK_NAME: str

    @property
    def is_empty(self):
        self_fields = fields(self)
        for field in self_fields:
            val = getattr(self, field.name)
            if val:
                return False
        return True
    
    def to_dict(self) -> dict[str, str | None]:
        ...

    @classmethod
    def parse(clazz, csv_text: str):
        # CSV reader doesn't work well for some reason
        vals = list(clazz(*row.split(';')) for row in csv_text.splitlines()[1:])
        vals = [val for val in vals if not val.is_empty]
        return vals


T = TypeVar("T", bound=ParsedFileType)

class VocabType(ParsedFileType):
    TYPE: str
    NOTE_TYPE = "French to English Noun"
    REVERSE_NOTE_TYPE = "English to French"
    DECK_NAME = "Vocab"
    REVERSE_DECK_NAME = "English to French Vocab"
    FIELDS = ["Word", "Masculine Singular", "Feminine Singular", "Masculine Plural", "Feminine Plural", "Adverb", "Infinitive", "Past Participle", "Present Participle", "Basic meanings of word", "Example sentences", "Wiktionary"]
    REVERSE_FIELDS = ["Basic meanings of word", "Masculine Singular", "Feminine Singular", "Masculine Plural", "Feminine Plural", "Adverb", "Infinitive", "Past Participle", "Present Participle", "Example sentences", "Wiktionary"]

    @staticmethod
    def format_wiki_link(word: str, wiktionary: str | None):
        return f'https://en.wiktionary.org/wiki/{word}#French'


@dataclass(frozen=True)
class NounVocab(VocabType):
    TYPE = "Nouns"

    word: str
    mas_sing: str | None
    fem_sing: str | None
    mas_plu: str | None
    fem_plu: str | None
    meanings: str
    examples: str | None
    wiktionary: str | None

    def to_dict(self):
        return {
            "Word": self.word,
            "Masculine Singular": self.mas_sing,
            "Feminine Singular": self.fem_sing,
            "Masculine Plural": self.mas_plu,
            "Feminine Plural": self.fem_plu,
            "Basic meanings of word": self.meanings,
            "Example sentences": self.examples,
            "Wiktionary": self.wiktionary,
        }


@dataclass(frozen=True)
class AdjectiveVocab(VocabType):
    TYPE = "Adjectives"

    word: str
    mas_sing: str | None
    fem_sing: str | None
    mas_plu: str | None
    fem_plu: str | None
    meanings: str
    examples: str | None
    wiktionary: str | None

    def to_dict(self):
        return {
            "Word": self.word,
            "Masculine Singular": self.mas_sing,
            "Feminine Singular": self.fem_sing,
            "Masculine Plural": self.mas_plu,
            "Feminine Plural": self.fem_plu,
            "Basic meanings of word": self.meanings,
            "Example sentences": self.examples,
            "Wiktionary": self.wiktionary,
        }

@dataclass(frozen=True)
class VerbVocab(VocabType):
    TYPE = "Verbs"

    word: str
    past_part: str
    present_part: str
    meanings: str
    examples: str | None
    wiktionary: str | None

    def to_dict(self):
        return {
            "Word": self.word,
            "Infinitive": self.word,
            "Past Participle": self.past_part,
            "Present Participle": self.present_part,
            "Basic meanings of word": self.meanings,
            "Example sentences": self.examples,
            "Wiktionary": self.wiktionary,
        }


@dataclass(frozen=True)
class AdverbVocab(VocabType):
    TYPE = "Adverbs"

    word: str
    meanings: str
    examples: str | None
    wiktionary: str | None

    def to_dict(self):
        return {
            "Word": self.word,
            "Adverb": self.word,
            "Basic meanings of word": self.meanings,
            "Example sentences": self.examples,
            "Wiktionary": self.wiktionary,
        }


@dataclass(frozen=True)
class MiscVocab(VocabType):
    TYPE = "Misc"

    word: str
    meanings: str
    examples: str | None
    wiktionary: str | None

    def to_dict(self):
        return {
            "Word": self.word,
            "Adverb": self.word,
            "Basic meanings of word": self.meanings,
            "Example sentences": self.examples,
            "Wiktionary": self.wiktionary,
        }


@dataclass(frozen=True)
class AdjectivePreposition(ParsedFileType):
    FIELDS = ["Key", "Adjective", "Complement", "Preposition", "Example"]
    NOTE_TYPE = "Adjective Prepositions"
    DECK_NAME = "Adjective Prepositions"

    adjective: str
    complement: str
    preposition: str
    example: str

    def to_dict(self):
        return {
            "Key": f"{self.adjective}-{self.complement}",
            "Adjective": self.adjective,
            "Complement": self.complement,
            "Preposition": self.preposition,
            "Example": self.example,
        }


@dataclass(frozen=True)
class VerbPreposition(ParsedFileType):
    FIELDS = ["Verb", "Prolative Usage", "A Usage", "De Usage", "Avec Usage"]
    NOTE_TYPE = "Verb Prepositions"
    DECK_NAME = "Verb Prepositions"

    verb: str
    prolative_usage: str | None
    a_usage: str | None
    de_usage: str | None
    avec_usage: str | None

    def to_dict(self):
        return {
            "Verb": self.verb,
            "Prolative Usage": self.prolative_usage,
            "A Usage": self.a_usage,
            "De Usage": self.de_usage,
            "Avec Usage": self.avec_usage,
        }


class Generator(Protocol):
    def generate_files(self, src_dir: Path, dest_dir: Path):
        for d in src_dir.iterdir():
            if not d.is_dir():
                continue

            deck = d.name
            dest_deck_dir = dest_dir / deck
            dest_deck_dir.mkdir(parents=True, exist_ok=True)

            def read_files(files: Iterable[Path]):
                file_contents: list[tuple[str, str]] = []

                for file in files:
                    if not file.is_file():
                        continue

                    file_contents.append((file.name, file.read_text()))
                
                return file_contents
            
            for f in FileType:
                src = d / (f.value + ".csv")
                if src.is_file():
                    files = read_files([src])
                else:
                    src_dir = d / f.value
                    if not src_dir.is_dir():
                        continue

                    files = read_files(src_dir.iterdir())
                
                self.generate(f, deck, dest_deck_dir, files)

    def parse_vocab_file(self, filename: str, csv_text: str) -> Sequence[VocabType]:
        vocab_types = {
            "nouns.csv": NounVocab,
            "adjectives.csv": AdjectiveVocab,
            "verbs.csv": VerbVocab,
            "adverbs.csv": AdverbVocab,
            "misc.csv": MiscVocab,
        }

        if filename not in vocab_types:
            raise NotImplementedError(f"Unsupported vocab file: {filename}")
        
        return self.parse_csv_file(vocab_types[filename], filename, csv_text)
    
    def parse_csv_file(self, typ: T, filename: str, csv_text: str) -> Sequence[T]:
        csv_lines = csv_text.splitlines()
        header = csv_lines[0]
        columns = header.split(';')
        if len(columns) <= 1:
            raise RuntimeError(f"Columns were not split by ';': {header}")
        return typ.parse(csv_text)

    
    def generate(self, type: FileType, deck_folder: str, dest_deck_dir: Path, files: list[tuple[str, str]]):
        ...



class AnkiGenerator(Generator):
    DECK_PREFIX = "French Courses"

    def format_deck_name(self, *deck_parts: str):
        return "::".join([self.DECK_PREFIX, *deck_parts])

    def format_grammar_file(self, md_text: str):
        md_lines = md_text.splitlines()
        header = md_lines[0]
        if not header.startswith("# "):
            raise RuntimeError(f"Unexpected header: {header}")
        
        title = header[2:]

        md = marko.Markdown()
        doc = md.parse("\n".join(md_lines[1:]))
        html_content = md.render(doc).replace("\n", "")

        return f"{title}|{html_content}"
    
    def format_grammar_files(self, deck_folder: str, grammar_files: list[tuple[str, str]]):
        dest_lines = [
            "#separator:Pipe",
            "#columns:Title|Content",
            "#notetype:French Grammar",
            f"#deck:{self.format_deck_name(deck_folder, 'Grammar')}",
        ]
        
        formatted_lines = [self.format_grammar_file(gf[1]) for gf in grammar_files]
        dest_lines.extend(sorted(formatted_lines))
        return "\n".join(dest_lines)

    
    def generate_grammar(self, deck_folder: str, dest_file: Path, grammar_files: list[tuple[str, str]]):
        dest_file.write_text(self.format_grammar_files(deck_folder, grammar_files))
    
    def format_vocab(self, vocab: VocabType, fields: list[str]):
        word_dict = vocab.to_dict()
        word_fields: list[str] = []
        for field in fields:
            word_fields.append(word_dict.get(field, "") or "")
        return "|".join(word_fields)
    
    
    def format_vocab_files(self, notetype: str, deck_path: list[str], vocab_files: list[tuple[str, str]], fields: list[str]):
        dest_lines = [
            "#separator:Pipe",
            "#columns:" + "|".join(fields),
            f"#notetype:{notetype}",
            f"#deck:{self.format_deck_name(*deck_path)}",
        ]

        formatted_lines: list[str] = []

        for vocab_file, vocab_text in vocab_files:
            parsed_lines = self.parse_vocab_file(vocab_file, vocab_text)
            formatted_lines.extend([self.format_vocab(line, fields) for line in parsed_lines])

        dest_lines.extend(sorted(formatted_lines))
        return "\n".join(dest_lines)
    
    def generate_vocab(self, deck_folder: str, dest_deck_dir: Path, vocab_files: list[tuple[str, str]]):
        dest_file = dest_deck_dir / "vocab.txt"
        dest_file.write_text(self.format_vocab_files(VocabType.NOTE_TYPE, [deck_folder, VocabType.DECK_NAME], vocab_files, VocabType.FIELDS))

        reverse_dest_file = dest_deck_dir / "reverse-vocab.txt"
        reverse_dest_file.write_text(self.format_vocab_files(VocabType.REVERSE_NOTE_TYPE, [deck_folder, VocabType.REVERSE_DECK_NAME], vocab_files, VocabType.REVERSE_FIELDS))
    
    def generate_parsed_file(self, deck_folder: str, dest_file: Path, typ: T, files: list[tuple[str, str]]):
        if not files:
            return
        
        if len(files) != 1:
            raise RuntimeError(f"Expected exactly one {str(typ)} file, got: {len(files)}")
        
        parsed = self.parse_csv_file(typ, *files[0])

        dest_lines = [
            "#separator:Pipe",
            "#columns:" + "|".join(typ.FIELDS),
            f"#notetype:{typ.NOTE_TYPE}",
            f"#deck:{self.format_deck_name(deck_folder, typ.DECK_NAME)}",
        ]

        for line in parsed:
            values = line.to_dict()
            dest_lines.append("|".join([values.get(f, "") or "" for f in typ.FIELDS]))
        
        dest_file.write_text("\n".join(dest_lines))
    
    def generate(self, type: FileType, deck_folder: str, dest_deck_dir: Path, files: list[tuple[str, str]]):
        if type == FileType.Grammar:
            self.generate_grammar(deck_folder, dest_deck_dir / "grammar.txt", files)
        elif type == FileType.Vocab:
            self.generate_vocab(deck_folder, dest_deck_dir, files)
        elif type == FileType.AdjectivePreposition:
            self.generate_parsed_file(deck_folder, dest_deck_dir / "adjective-preposition.txt", AdjectivePreposition, files)
        elif type == FileType.VerbPreposition:
            self.generate_parsed_file(deck_folder, dest_deck_dir / "verb-preposition.txt", VerbPreposition, files)
        else:
            raise NotImplementedError(f"File type {type} is not supported for Anki generation.")


class MarkdownGenerator(Generator):
    def generate_grammar(self, dest_deck_dir: Path, grammar_files: list[tuple[str, str]]):
        for grammar_file, grammar_text in grammar_files:
            dest_file = dest_deck_dir / grammar_file
            dest_file.write_text(grammar_text)
    
    def format_vocab_file(self, parsed_lines: Sequence[VocabType]):
        formatted_lines: list[str] = []

        if not parsed_lines:
            return formatted_lines
        
        first = parsed_lines[0]
        formatted_lines.append(f"## {first.TYPE}")

        fields = first.to_dict().keys()
        fields = [f for f in VocabType.FIELDS if f in fields]
        formatted_lines.append("| " + " | ".join(fields) + " |")
        formatted_lines.append("| " + " | ".join(["---"] * len(fields)) + " |")
        for line in parsed_lines:
            values = line.to_dict()
            values["Wiktionary"] = f"[Link](<{VocabType.format_wiki_link(values['Word'], values['Wiktionary'])}>)"
            formatted_lines.append("| " + " | ".join([values[f] for f in fields]) + " |")
        
        return formatted_lines
    
    def format_vocab_files(self, vocab_files: list[tuple[str, str]]):
        formatted_lines = ["# Vocabulary"]

        for vocab_file, vocab_text in sorted(vocab_files):
            parsed_lines = self.parse_vocab_file(vocab_file, vocab_text)
            formatted_lines.extend(self.format_vocab_file(parsed_lines))
        
        return "\n".join(formatted_lines)

    def generate_vocab(self, dest_deck_dir: Path, vocab_files: list[tuple[str, str]]):
        dest_file = dest_deck_dir / "vocab.md"
        dest_file.write_text(self.format_vocab_files(vocab_files))
    
    def format_parsed_file(self, typ: T, parsed_lines: Sequence[T]):
        formatted_lines: list[str] = []

        formatted_lines.append(f"# {typ.DECK_NAME}")
        formatted_lines.append("")

        fields = typ.FIELDS
        if "Key" in fields:
            del fields[fields.index("Key")]

        formatted_lines.append("| " + " | ".join(fields) + " |")
        formatted_lines.append("| " + " | ".join(["---"] * len(fields)) + " |")
        for line in parsed_lines:
            values = line.to_dict()
            formatted_lines.append("| " + " | ".join([values.get(f, "") for f in fields]) + " |")
        return "\n".join(formatted_lines)
    
    def generate_parsed_file(self, dest_file: Path, typ: T, files: list[tuple[str, str]]):
        if not files:
            return
        
        if len(files) != 1:
            raise RuntimeError(f"Expected exactly one {str(typ)} file, got: {len(files)}")
        
        dest_file.write_text(self.format_parsed_file(typ, self.parse_csv_file(typ, *files[0])))
    
    def generate(self, type: FileType, deck_folder: str, dest_deck_dir: Path, files: list[tuple[str, str]]):
        if type == FileType.Grammar:
            self.generate_grammar(dest_deck_dir, files)
        elif type == FileType.Vocab:
            self.generate_vocab(dest_deck_dir, files)
        elif type == FileType.AdjectivePreposition:
            self.generate_parsed_file(dest_deck_dir / "adjective-preposition.md", AdjectivePreposition, files)
        elif type == FileType.VerbPreposition:
            self.generate_parsed_file(dest_deck_dir / "verb-preposition.md", VerbPreposition, files)
        else:
            print(f"File type {type} is not supported for Markdown generation.")


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
    
    AnkiGenerator().generate_files(src_dir, anki_dir)
    MarkdownGenerator().generate_files(src_dir, md_dir)
