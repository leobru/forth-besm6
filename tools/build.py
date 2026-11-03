#!/usr/bin/env python3
"""Assemble BEMSH sources with ИПМ МАКРО-БЕМШ 06/78 under dispak and write
the program image with ЗОНГП to a private disk; then write a terminal run deck.

Usage: tools/build.py [--name forth] [--start 10] SOURCE.be [MORE.be ...]
Outputs (in build/): NAME.lst (assembler listing), disk/DISK (image zones),
NAME.b6 (run deck: Э70 each zone, then jump to the start address).
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
DISK = '1234'           # private image volume, unit 043
SYSTEM = '/usr/local/share/besm6'

HEADER = '''шифр 419999^
трак 64^
лент 30(2048-6200)^
лент 42(2099)^
лент 43({disk}-ЗП)^
ацп 40^
росп 0^
врем 240^
лист 0-37^
вход 4000^
е
в 4000
к 00 010 4003
к 15 24 04000
к 00 066 0001 00 000 0100
с 3000 67
в 14000
а1
ВВД$$$^
'''
TAIL = '''КВЧ$$$^
ТРН$$$^
0-0^
ЧТКОМП420070^
НАЗ   {start:06o}^
ЗОНГП 430001  000001^
КНЦ$$$^
_$ЕКОНЕЦ
'''
# Run deck: a loader at 077700 reads each zone (zone k+1 -> page k) and
# jumps to the start.  Control words for Э70 sit at 077740...
RUN = '''шифр 419999^
озу 32^
{time}лент 43({disk})^
тел^
вход 77700^
е
в 77700
{loads}к 00 30 {start:05o}
в 77740
{cws}е
еконец
'''


def check_card(path, n, line):
    # BEMSH reads columns 1-64 only (the rest is dropped without an error)
    assert len(line) <= 64, f'{path}:{n}: card exceeds 64 columns'
    if line and not line[0].isspace() and not line.startswith('*'):
        assert len(line.split()[0]) <= 6, f'{path}:{n}: label exceeds six characters'


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('sources', nargs='+')
    ap.add_argument('--name', default='forth')
    ap.add_argument('--start', default='10', help='octal start (НАЗ) address')
    ap.add_argument('--time', help='run-deck time card value (none by default)')
    ap.add_argument('--limit', help='octal address the image must end below')
    ap.add_argument('--dispak', default=os.environ.get('DISPAK', 'dispak'))
    args = ap.parse_args()
    start = int(args.start, 8)
    lines = []
    for src in args.sources:
        for n, line in enumerate(Path(src).read_text().splitlines(), 1):
            check_card(src, n, line)
            lines.append(line)
    disks = BUILD / 'disk'
    home = BUILD / 'home'
    (home / '.besm6').mkdir(parents=True, exist_ok=True)
    disks.mkdir(parents=True, exist_ok=True)
    image = disks / DISK
    image.write_bytes(b'')
    deck = BUILD / (args.name + '-asm.b6')
    deck.write_text(HEADER.format(disk=DISK) + ''.join(l + '^\n' for l in lines)
                    + TAIL.format(start=start))
    env = dict(os.environ, HOME=str(home))
    env.pop('BESM6_PATH', None)
    env.pop('BESM6_SMALL_DISKS', None)
    listing = BUILD / (args.name + '.lst')
    with listing.open('w') as out:
        r = subprocess.run([args.dispak, '--path=%s:%s' % (disks, SYSTEM), '-l', str(deck)],
                           cwd=BUILD, env=env, stdin=subprocess.DEVNULL, stdout=out,
                           stderr=subprocess.STDOUT, timeout=120)
    text = listing.read_text(encoding='utf-8-sig').translate(
        str.maketrans('ABCEHKMOPTXY', 'АВСЕНКМОРТХУ'))
    errors = [int(n) for n in re.findall(r'ОШИБОК\s*=\s*(\d+)', text)]
    if r.returncode or not errors or any(errors) or 'АВОСТ' in text:
        raise SystemExit(f'BEMSH failed (errors {errors}); see {listing}')
    m = re.search(r'ЗОНГП\s*=\s*43(\d{4})\s+СВ\.ЗОНА\s*=\s*43(\d{4})\s+'
                  r'АМИН=(\d+)\s+АМАКС=(\d+)', text)
    if not m:
        raise SystemExit(f'no ЗОНГП line; see {listing}')
    first, free = int(m.group(1), 8), int(m.group(2), 8)
    amin, amax = int(m.group(3), 8), int(m.group(4), 8)
    nz = free - first
    if args.limit and amax >= int(args.limit, 8):
        raise SystemExit(f'image ends at {amax:05o}, overlapping {args.limit}')
    page0 = amin // 1024
    assert amax < 0o77700 and nz <= 0o37, 'image collides with the loader'
    loads = ''.join('к 00 170 %04o\n' % (0o7740 + i) for i in range(nz))
    cws = ''.join('с 0010 %04o 0043 %04o\n' % ((page0 + i) << 6, first + i)
                  for i in range(nz))
    run = BUILD / (args.name + '.b6')
    run.write_text(RUN.format(disk=DISK, start=start, loads=loads, cws=cws,
                              time='врем %s^\n' % args.time if args.time else ''))
    print(f'BEMSH: 0 errors; АМИН={amin:05o} АМАКС={amax:05o}; {nz} zone(s); {run}')


if __name__ == '__main__':
    main()
