#!/usr/bin/env python3
"""ASCII <-> GOST 10859 as dispak's terminal maps it, and BEMSH text constants.

Usage:
  tools/gost.py 'HELLO, WORLD'        # КОНД lines, text ended by 0172
  tools/gost.py -n 'ABC'              # no terminator; zero padding
The ASCII table is dispak/encoding.c unicode_to_gost (tab0), lowercase folded.
"""
import sys

_ASCII = {
    ' ': 0o17, '!': 0o133, '"': 0o134, '#': 0o34, '$': 0o127, '%': 0o126,
    '&': 0o121, "'": 0o33, '(': 0o22, ')': 0o23, '*': 0o31, '+': 0o12,
    ',': 0o15, '-': 0o13, '.': 0o16, '/': 0o14, ':': 0o37, ';': 0o26,
    '<': 0o35, '=': 0o25, '>': 0o36, '?': 0o136, '@': 0o21, '[': 0o27,
    '\\': 0o175, ']': 0o30, '^': 0o115, '_': 0o132, '`': 0o32, '{': 0o125,
    '|': 0o130, '~': 0o123,
    'A': 0o40, 'B': 0o42, 'C': 0o61, 'D': 0o77, 'E': 0o45, 'F': 0o100,
    'G': 0o101, 'H': 0o55, 'I': 0o102, 'J': 0o103, 'K': 0o52, 'L': 0o104,
    'M': 0o54, 'N': 0o105, 'O': 0o56, 'P': 0o60, 'Q': 0o106, 'R': 0o107,
    'S': 0o110, 'T': 0o62, 'U': 0o111, 'V': 0o112, 'W': 0o113, 'X': 0o65,
    'Y': 0o63, 'Z': 0o114,
}
for _d in range(10):
    _ASCII[str(_d)] = _d
for _i, _ch in enumerate('АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЫЬЭЮЯ'):
    _ASCII[_ch] = 0o40 + _i
_ASCII['Ъ'] = 0o135
_ASCII['Ё'] = _ASCII['Е']

END = 0o172      # end of information: output stops (newline unless prompt)
EOL = 0o377      # end of an input line


def encode(text):
    """ASCII text -> list of GOST codes (lowercase folded, unknown -> error)."""
    out = []
    for ch in text:
        c = ch.upper()
        if c not in _ASCII:
            raise ValueError('no GOST code for %r' % ch)
        out.append(_ASCII[c])
    return out


def words(codes, pad=0):
    """Pack codes 6 per word, big-endian, padding the last word."""
    codes = list(codes)
    while len(codes) % 6:
        codes.append(pad)
    return [int.from_bytes(bytes(codes[i:i + 6]), 'big')
            for i in range(0, len(codes), 6)]


def kond(ws):
    return ['\tКОНД\tВ\'%016o\'' % w for w in ws]


def main():
    args = sys.argv[1:]
    term = True
    if args and args[0] == '-n':
        term = False
        args = args[1:]
    codes = encode(' '.join(args))
    if term:
        codes.append(END)
    print('\n'.join(kond(words(codes))))


if __name__ == '__main__':
    main()
