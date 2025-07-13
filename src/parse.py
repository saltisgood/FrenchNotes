from parser.extensions import BlueElem, TableBlock
from parser.html_renderer import HtmlRendererMixin

import marko

from argparse import ArgumentParser

def _main(file: str, print_only: bool):
    with open(file, encoding="UTF-8") as f:
        raw_md = f.read()
    
    extended_html = marko.MarkoExtension(
        elements=[BlueElem, TableBlock],
        renderer_mixins=[HtmlRendererMixin],
    )
    
    markdown = marko.Markdown(extensions=[extended_html])
    doc = markdown.parse(raw_md)
    print(markdown.render(doc))
    
    # doc = marko.parse(raw_md)
    # print(marko.render(doc))

if __name__ == "__main__":
    _main("B1.2/Grammar/les pronoms possessifs.md", True)