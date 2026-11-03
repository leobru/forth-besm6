#!/usr/bin/env python3
"""Check that the prelude words in the BEMSH listing equal the GOST text of
lib/core.fs as mkforth.py prepares it (BEMSH drops a card silently at ? or \\).

Usage: tools/chkprelude.py build/forth.lst lib/core.fs
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gost
import mkforth


def main():
    lst, core = sys.argv[1], sys.argv[2]
    text = mkforth.prelude_text(core)
    exp = gost.words(gost.encode(text))
    words, base = {}, None
    for line in open(lst, encoding='utf-8', errors='replace'):
        m = re.match(r'^[ 0-9]*?[ _‾]([0-7]{5})  ([0-7]{16})( |$)', line)
        if m:
            words.setdefault(int(m.group(1), 8), int(m.group(2), 8))
        m = re.search(r'(?:^|\s)П[PР][EЕ]Л +([0-7]{5}) ', line)   # symbols
        if m:
            base = int(m.group(1), 8)
    if base is None:
        sys.exit('%s: no ПРЕЛ in the symbol table' % lst)
    bad = [i for i, w in enumerate(exp) if words.get(base + i) != w]
    if bad:
        i = bad[0]
        sys.exit('prelude word %d (%05o) is %s, expected %016o %r' % (
            i, base + i, '%016o' % words[base + i] if base + i in words
            else 'missing', exp[i], text[6 * i:6 * i + 6]))
    print('prelude: %d words match' % len(exp))


if __name__ == '__main__':
    main()
