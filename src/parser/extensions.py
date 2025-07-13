from marko import block, inline, source

import re

class BlueElem(inline.InlineElement):
    pattern = r'<blue>(.+)</blue>'
    parse_children = True
    override = True
    priority = 10


class TableBlock(block.BlockElement):
    pattern = re.compile(r'^| (.*) |$', re.M)

    def __init__(self, match):
        print("Found table")

    @classmethod
    def match(cls, source: source.Source):
        print("Testing table: " + (source.next_line() or "") + "(end)")
        m = source.expect_re(cls.pattern)
        if not m:
            return None
        
