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
SAFECODE = {gost.encode(c)[0]: c for c in TEXTSAFE}
# Codes with no ASCII input character that BEMSH also reads there: 020 is
# ⏨, 034 is # (or ≠).  024 (× and \\* give 0121) and 032 (‘ closes the
# text) cannot be written.  So all name lengths but 20 and 26 are characters.
SAFECODE.update({0o20: '⏨', 0o34: '#'})
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def header_lines(label, prev, name, immediate):
    codes = gost.encode(name)
    assert 0 < len(codes) <= 31, name
    first = len(codes) | (0o200 if immediate else 0)
    out = ['%s\tКОНД\t%s' % (label, 'А(%s)' % prev if prev else "В'0'")]
    out += data_cards([first] + codes)
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


def kond_word(codes):
    """КОНД operand for one word of 6 GOST codes, as П'...'.  A code with no
    character BEMSH reads there (? and \\ end the card; also lengths and
    flags) is 0 in П'...' and is added as Мshift В'code' (no М0 for the
    last byte): П'Q0QW0W'М32В'136'М8В'175' is "Q?QW\\W"."""
    lit = ''.join(SAFECODE.get(c, '0') for c in codes).replace("'", "''")
    return "П'%s'" % lit + ''.join(
        ("М%d" % (8 * (5 - i)) if i < 5 else '') + "В'%o'" % c
        for i, c in enumerate(codes) if c not in SAFECODE)


def data_cards(codes, label=''):
    """Cards for GOST codes packed 6 per word, zero padded: runs of words
    that are all characters become ТЕКСТ П'...' (ending by column 63, BEMSH
    «СИМВОЛОВ >63»: at most 8 words); other words are КОНД (kond_word).  LABEL goes on the first card."""
    codes = list(codes) + [0] * (-len(codes) % 6)
    out, run = [], []

    def lab():
        return '' if out else label

    def text(words):
        return "%s ТЕКСТ П'%s'" % (lab(), ''.join(
            SAFECODE[c] for w in words for c in w).replace("'", "''"))

    def flush():
        if run:
            out.append(text(run))
        run.clear()

    for i in range(0, len(codes), 6):
        w = codes[i:i + 6]
        if all(c in SAFECODE for c in w):
            if len(text(run + [w])) > 63:
                flush()
            run.append(w)
        else:
            flush()
            out.append('%s КОНД %s' % (lab(), kond_word(w)))
    flush()
    return out


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
            out += data_cards([len(tc)] + tc, label)
        elif line.strip() == '*PRELUDE':
            out += data_cards(gost.encode(ptext), 'ПРЕЛ') or ["ПРЕЛ КОНД В'0'"]
        elif line.strip() == '*PRELEN':
            out.append("ДЛПРЕЛ\tКОНД\tВ'%o'" % len(ptext))
        else:
            out.append(line)
    print('\n'.join(out))


if __name__ == '__main__':
    main()
