#!/usr/bin/env python3
"""Expand forth.be into plain BEMSH: dictionary headers, tables, prelude.

Usage: tools/mkforth.py forth.be lib/core.fs > build/forth-gen.be

Directives (comment cards to BEMSH, so the source stays readable):
  *: NAME LABEL [I]   header for Forth word NAME whose code starts at LABEL
                      (the next card must carry LABEL); I = IMMEDIATE.
  *LAST               becomes  ПОСЛ КОНД А(<last header>)
  *DIGITS             GOST code -> digit value table (ЦИФТ), digit value
                      -> GOST code table (ЦИФВ), name length -> words (НСЛТ)
  *TEXT LABEL "text"  counted GOST string
  *PRELUDE            lib/core.fs at ПРЕЛ as ТЕКСТ П'...' cards: lines
                      joined by a blank, \\ comment lines dropped
  *PRELEN             ДЛПРЕЛ КОНД <its length in characters>
Header layout: word 0 = link to previous header (А(...)); then the name as a
counted string, 6 GOST bytes per word, zero padded; byte 0 = length, 0200 =
IMMEDIATE, 0100 = hidden.  Code (the xt) follows the last name word.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gost

# Characters BEMSH reads inside П'...' (checked in the listing); ? and \
# end the card, silently.
TEXTSAFE = set(" !\"'()*+,-./0123456789:;<=>@[]" + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def header_lines(label, prev, name, immediate):
    codes = gost.encode(name)
    assert 0 < len(codes) <= 31, name
    first = len(codes) | (0o200 if immediate else 0)
    words = gost.words([first] + codes)
    out = ['%s\tКОНД\t%s' % (label, 'А(%s)' % prev if prev else "В'0'")]
    out += gost.kond(words)
    return out


def digit_tables():
    val = [0o77] * 0o115
    for d in range(10):
        val[d] = d
    for i, ch in enumerate(LETTERS):
        val[gost.encode(ch)[0]] = 10 + i
    out = ['* ГОСТ-код литеры -> значение цифры (077 - не цифра)']
    out += ["%s\tКОНД\tВ'%o'" % ('ЦИФТ' if i == 0 else '', v) for i, v in enumerate(val)]
    out += ['* значение цифры -> ГОСТ-код литеры']
    chars = gost.encode('0123456789' + LETTERS)
    out += ["%s\tКОНД\tВ'%o'" % ('ЦИФВ' if i == 0 else '', c) for i, c in enumerate(chars)]
    out += ['* длина имени -> число слов счётной строки: (n+6)/6']
    out += ["%s\tКОНД\tВ'%o'" % ('НСЛТ' if n == 0 else '', (n + 6) // 6) for n in range(32)]
    return out


def prelude_text(path):
    """lib/core.fs as one string: lines joined by a blank, padded with
    blanks to whole words.

    \\ comment lines are dropped: BEMSH text constants cannot hold the
    newline that would end them.
    """
    out = []
    for n, line in enumerate(Path(path).read_text().splitlines(), 1):
        line = line.strip().upper()
        if not line or line.split()[0] == '\\':
            continue
        if '\\' in line.split()[1:] and not line.startswith(': \\ '):
            raise SystemExit('%s:%d: only whole-line \\ comments' % (path, n))
        try:
            gost.encode(line)
        except ValueError as e:
            raise SystemExit('%s:%d: %s' % (path, n, e))
        out.append(line)
    text = ' '.join(out)
    return text + ' ' * (-len(text) % 6)


def kond_text(ch):
    """КОНД operand for 6 characters, some of which end a BEMSH card: they
    are 0 in П'...' and added as Мshift В'code' (no М0 for the last one):
    П'Q0QW0W'М32В'136'М8В'175' is "Q?QW\\W"."""
    lit = ''.join(c if c in TEXTSAFE else '0' for c in ch).replace("'", "''")
    return "П'%s'" % lit + ''.join(
        ("М%d" % (8 * (5 - i)) if i < 5 else '') + "В'%o'" % gost.encode(c)[0]
        for i, c in enumerate(ch) if c not in TEXTSAFE)


def prelude_lines(text):
    """ТЕКСТ П'...' cards ending by column 63 (BEMSH: «СИМВОЛОВ >63»), so
    at most 8 words each.  A word with a character that ends a BEMSH card
    (? and \\) becomes КОНД (kond_text)."""
    out, run = [], []

    def card(chunks):
        lab = 'ПРЕЛ' if not out else ''
        return "%s ТЕКСТ П'%s'" % (lab, ''.join(chunks).replace("'", "''"))

    for i in range(0, len(text), 6):
        ch = text[i:i + 6]
        if set(ch) <= TEXTSAFE and len(card(run + [ch])) <= 63:
            run.append(ch)
            continue
        if run:
            out.append(card(run))
            run = []
        if set(ch) <= TEXTSAFE:
            run = [ch]
        else:
            out.append(('ПРЕЛ' if not out else '') + ' КОНД ' + kond_text(ch))
    if run:
        out.append(card(run))
    return out or ["ПРЕЛ КОНД В'0'"]


def main():
    src, core = sys.argv[1], sys.argv[2]
    out, prev, n = [], None, 0
    ptext = prelude_text(core)
    lines = Path(src).read_text().splitlines()
    last = 'Ш%03d' % sum(l.startswith('*: ') for l in lines)
    for line in lines:
        if line.startswith('*: '):
            parts = line[3:].split()
            name, label = parts[0], parts[1]
            imm = len(parts) > 2 and parts[2] == 'I'
            n += 1
            hl = 'Ш%03d' % n
            out += header_lines(hl, prev, name, imm)
            prev = hl
        elif line.strip() == '*LAST':
            out.append('ПОСЛ\tКОНД\tА(%s)' % last)
        elif line.strip() == '*DIGITS':
            out += digit_tables()
        elif line.startswith('*TEXT '):
            _, label, text = line.split(None, 2)
            assert text[0] == '"' and text[-1] == '"', line
            tc = gost.encode(text[1:-1])
            k = gost.kond(gost.words([len(tc)] + tc))
            out += [label + k[0]] + k[1:]
        elif line.strip() == '*PRELUDE':
            out += prelude_lines(ptext)
        elif line.strip() == '*PRELEN':
            out.append("ДЛПРЕЛ\tКОНД\tВ'%o'" % len(ptext))
        else:
            out.append(line)
    print('\n'.join(out))


if __name__ == '__main__':
    main()
