import marko

from argparse import ArgumentParser
from dataclasses import dataclass, fields
from enum import Enum, StrEnum
from pathlib import Path
from shutil import rmtree
from typing import Protocol

VOCAB_FIELDS = ["Word", "Masculine Singular", "Feminine Singular", "Masculine Plural", "Feminine Plural", "Adverb", "Infinitive", "Past Participle", "Present Participle", "Basic meanings of word", "Example sentences", "Wiktionary"]
REVERSE_VOCAB_FIELDS = ["Basic meanings of word", "Masculine Singular", "Feminine Singular", "Masculine Plural", "Feminine Plural", "Adverb", "Infinitive", "Past Participle", "Present Participle", "Example sentences", "Wiktionary"]



class VocabType:
    @property
    def is_empty(self):
        self_fields = fields(self)
        for field in self_fields:
            val = getattr(self, field.name)
            if val:
                return False
        return True

    @classmethod
    def parse(clazz, csv_text: str):
        # CSV reader doesn't work well for some reason
        vals = list(clazz(*row.split(';')) for row in csv_text.splitlines()[1:])
        vals = [val for val in vals if not val.is_empty]
        return vals


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


class Generator(Protocol):
    def generate_files(self, src_dir: Path, dest_dir: Path):
        for d in src_dir.iterdir():
            if not d.is_dir():
                continue

            deck = d.name
            dest_deck_dir = dest_dir / deck
            dest_deck_dir.mkdir(parents=True, exist_ok=True)

            def read_files(subdir: Path):
                grammar_files: list[tuple[str, str]] = []

                for grammar_file in subdir.iterdir():
                    if not grammar_file.is_file():
                        continue

                    grammar_files.append((grammar_file.name, grammar_file.read_text()))
                
                return grammar_files

            src_grammar = d / "Grammar"
            if src_grammar.exists():
                grammar_files = read_files(src_grammar)
                self.generate_grammar(dest_deck_dir, grammar_files)
            
            src_vocab = d / "Vocab"
            if src_vocab.exists():
                vocab_files = read_files(src_vocab)
                self.generate_vocab(dest_deck_dir, vocab_files)

    def parse_vocab_file(self, filename: str, csv_text: str):
        csv_lines = csv_text.splitlines()
        header = csv_lines[0]
        columns = header.split(';')
        if len(columns) <= 1:
            raise RuntimeError(f"Columns were not split by ';': {header}")
        
        if filename == "nouns.csv":
            return NounVocab.parse(csv_text)
        elif filename == "adjectives.csv":
            return AdjectiveVocab.parse(csv_text)
        elif filename == "verbs.csv":
            return VerbVocab.parse(csv_text)
        elif filename == "adverbs.csv":
            return AdverbVocab.parse(csv_text)
        elif filename == "misc.csv":
            return MiscVocab.parse(csv_text)
        else:
            raise NotImplementedError(filename)
    
    def generate_grammar(self, dest_deck_dir: Path, grammar_files: list[tuple[str, str]]):
        ...
    
    def generate_vocab(self, dest_deck_dir: Path, vocab_files: list[tuple[str, str]]):
        ...



class AnkiGenerator(Generator):
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
    
    def format_grammar_files(self, grammar_files: list[tuple[str, str]]):
        dest_lines = [
            "#separator:Pipe",
            "#columns:Title|Content",
        ]
        
        formatted_lines = [self.format_grammar_file(gf[1]) for gf in grammar_files]
        dest_lines.extend(sorted(formatted_lines))
        return "\n".join(dest_lines)

    
    def generate_grammar(self, dest_deck_dir: Path, grammar_files: list[tuple[str, str]]):
        dest_file = dest_deck_dir / "grammar.txt"
        dest_file.write_text(self.format_grammar_files(grammar_files))
    
    def format_vocab(self, vocab: NounVocab | AdjectiveVocab | VerbVocab | AdverbVocab | MiscVocab, fields: list[str]):
        word_dict = vocab.to_dict()
        word_fields: list[str] = []
        for field in fields:
            word_fields.append(word_dict.get(field, "") or "")
        return "|".join(word_fields)
    
    
    def format_vocab_files(self, vocab_files: list[tuple[str, str]], fields: list[str]):
        dest_lines = [
            "#separator:Pipe",
            "#columns:" + "|".join(fields),
        ]

        formatted_lines: list[str] = []

        for vocab_file, vocab_text in vocab_files:
            parsed_lines = self.parse_vocab_file(vocab_file, vocab_text)
            formatted_lines.extend([self.format_vocab(line, fields) for line in parsed_lines])

        dest_lines.extend(sorted(formatted_lines))
        return "\n".join(dest_lines)
    
    def generate_vocab(self, dest_deck_dir: Path, vocab_files: list[tuple[str, str]]):
        dest_file = dest_deck_dir / "vocab.txt"
        dest_file.write_text(self.format_vocab_files(vocab_files, VOCAB_FIELDS))

        reverse_dest_file = dest_deck_dir / "reverse-vocab.txt"
        reverse_dest_file.write_text(self.format_vocab_files(vocab_files, REVERSE_VOCAB_FIELDS))


class MarkdownGenerator(Generator):
    def generate_grammar(self, dest_deck_dir: Path, grammar_files: list[tuple[str, str]]):
        for grammar_file, grammar_text in grammar_files:
            dest_file = dest_deck_dir / grammar_file
            dest_file.write_text(grammar_text)
    
    def format_vocab_file(self, parsed_lines: list[NounVocab] | list[AdjectiveVocab] | list[VerbVocab] | list[AdverbVocab]):
        formatted_lines: list[str] = []

        if not parsed_lines:
            return formatted_lines
        
        first = parsed_lines[0]
        formatted_lines.append(f"## {first.TYPE}")

        fields = first.to_dict().keys()
        fields = [f for f in VOCAB_FIELDS if f in fields]
        formatted_lines.append("| " + " | ".join(fields) + " |")
        formatted_lines.append("| " + " | ".join(["---"] * len(fields)) + " |")
        for line in parsed_lines:
            values = line.to_dict()
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
