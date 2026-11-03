# FORTH for the BESM-6

An interactive Forth for the BESM-6 (БЭСМ-6). It runs as a terminal (`тел`)
task under the [dispak](https://github.com/besm6/dispak) emulator. The kernel
is written in BEMSH and assembled by the historical translator ИПМ МАКРО-БЕМШ
06/78 running under dispak. Higher-level words are written in Forth
([lib/core.fs](lib/core.fs)), stored in the image and interpreted at startup.

```
FORTH BESM-6
: SQ DUP * ;  7 SQ .
49  OK
: FIB DUP 2 < IF EXIT THEN DUP 1- RECURSE SWAP 2 - RECURSE + ;  20 FIB .
6765  OK
```

## Requirements

- `dispak` and the system volumes 2048 (BEMSH) and 2099 (macro library) in
  `/usr/local/share/besm6` (set `SYSTEM_DISKS` to override). Set `DISPAK` to
  select a binary.
- Python 3.

## Usage

```sh
make            # assemble; writes build/forth.lst, build/disk/1234, build/forth.b6
make run        # interactive session (dispak -l: Latin letters on output)
make test       # tests/*.fs against tests/*.out
make dialog     # scripted pty session (expect): prompt, ACCEPT, BYE
make probe      # the Э71 / memory / Э75 probe (probe/probe.be)
echo '2 3 + .' | tools/run-dispak.sh -l build/forth.b6
```

[tools/build.py](tools/build.py) runs two jobs:

1. **Assembly.** It runs BEMSH on `build/forth-gen.be`. `ЗОНГП 430001` writes
   the image, from page 0, to the private volume `build/disk/1234`. The
   build checks the listing for zero errors.
2. **Run deck.** It generates `build/forth.b6`, a `тел` job. Its loader at
   077700 reads each zone with Э70 and jumps to 00010.

[tools/run-dispak.sh](tools/run-dispak.sh) runs dispak with an isolated
`HOME` (`build/home`).

`BYE` ends the task. So does end of input.

## Terminal and text

- All text is GOST 10859.
- **Э71 output.** The terminal output buffer is packed six bytes per word.
  It ends with 0172 and is padded with 0143, which dispak ignores.
- **Э71 input with a prompt.** Text that is still in the output buffer when
  input is requested becomes the prompt. So `." NAME? " PAD 30 ACCEPT`
  prints the question on the same line as the reply.
- **Case and character mapping.** dispak folds input to upper case. It maps
  `@` → 021, `'` → 033, `\` → 0175 and so on, so on output they show as
  `↑`, `’` and a line break. Hex digits are the letters A–F; the digit table
  is generated from the GOST codes.
- **Strings are packed.**
  - A character address is `6*word + byte` (byte 0 is the leftmost).
  - A cell address is a plain word address.
  - `A>C` and `C>A` convert between the two.
  - `C@`, `C!`, `TYPE`, `COUNT`, `CMOVE`, `FILL`, `WORD`, `PARSE` and `S"`
    take character addresses.
  - `@`, `!`, `,`, `HERE`, `ALLOT` and `CREATE` bodies use cell addresses.

## Machine conventions

| Resource | Use |
|---|---|
| A (accumulator) | top of the data stack |
| M17 | data stack pointer (native stack), base 070010, grows up |
| M12 | return stack pointer, 074000 and up, points at the first free cell |
| M13 | link register of every `ПВ` (Forth call) |
| M14, M15 | scratch in primitives and in compiled code |
| M1, M2, M11 | link registers of kernel subroutines (two levels and leaf) |
| R | `НТР 3` (no normalization or rounding) throughout |

**Code generation (subroutine-threaded).** An execution token is the word
address of the code. The compiler keeps a half-word cursor (`HERE` plus a
half flag) and writes instruction words with **Э75**. A word written by `ЗП`
carries the data-word tag, and executing it stops the task with
«КОНТРОЛЬ КОМАНДЫ».

| Construct | Compiled code |
|---|---|
| call | `ПВ xt(М13)`; the return lands on the next word |
| `:` prologue | `СЧИМ М13` · `ЗПМ (М12)` · `СЛИА 1(М12)` (A is preserved) |
| `EXIT` / `;` | a call to EXIT: `СЛИА -1(М12)` · `МОД (М12)` · `ПБ` |
| literal 0…077777 | `УИА n(М14)` · `СЧИМ М14` |
| any other literal | `ПВ (LIT)(М13)` followed by a data word |
| `IF`, `UNTIL`, `WHILE` | `НЕД` · `УИМ М14` · `ПИО target(М14)` (any non-zero cell is true) |
| `ELSE`, `AGAIN` | `ПБ target` |
| `DO … LOOP` | `ПВ (DO)(М13)`, a LEAVE-address cell, the body, then `ПВ (LOOP)(М13)` and a loop-back cell. The return stack holds the LEAVE address, the limit and the index. |
| `CREATE` | `УИА body(М14)` · `СЧИМ М14` · `ПБ (М13)`; `DOES>` patches the third instruction to `ПБ does-code` |

**Dictionary headers.** Word 0 links to the previous header. Then comes the
name as a packed counted string; its first byte holds the length, 0200 for
IMMEDIATE and 0100 while hidden. The code follows. `FIND` compares whole
words.

**Integers.** Integers follow the v7besm C convention: exponent field 0 and a
41-bit two's-complement value, so the range is ±2⁴⁰.
- `+` and `-` use `СЛ`/`ВЧ` under `НТР 3`.
- `*`, `/` and `MOD` follow the runtime helpers b$mul, b$div and b$mod.
- Division truncates toward zero, so `-17 5 /MOD` gives −2 −3.
- TRUE is −1, which is 41 one-bits.
- Overflow beyond 41 bits is not modular.

**Memory map.**
- 00010–00405: constants, tables and variables, kept below 07777,
  which short-address instructions can reach.
- Then the kernel code and the GOST text of `lib/core.fs`. The image must
  end below 04000; `make` checks this.
- 04000–05203: buffers, declared with `ЭКВ` and not part of the image
  (output, ACCEPT input, terminal line, name).
- The dictionary starts at 05204.
- 070010 and up: the data stack. 074000 and up: the return stack.

The image starts at 00010 to stay compatible with a future ПУЛЬТ launcher.

## Source layout

- [forth.be](forth.be): the BEMSH kernel. It has 96 words, including
  the interpreter, the compiler and the terminal I/O. `lib/core.fs` adds 64.
- [tools/mkforth.py](tools/mkforth.py): turns `*: NAME LABEL [I]` lines into
  dictionary headers and generates the digit and name-length tables. It also
  embeds `lib/core.fs` as readable `ТЕКСТ П'…'` cards (see below).
- [lib/core.fs](lib/core.fs): control structures, `DO`/`LOOP`, number
  output, `."`, `S"`, `CONSTANT`, `VARIABLE`, `WORDS` and so on.
- [tools/chkprelude.py](tools/chkprelude.py): `make` compares the prelude
  words in the listing with the expected GOST text.
- [tools/gost.py](tools/gost.py): the ASCII/Cyrillic → GOST table (from
  dispak), packing, and `КОНД` text constants.

**The prelude in BEMSH.** The lines of `lib/core.fs` are joined by single
blanks into one text, which is cut into `ТЕКСТ П'…'` cards. `\` comment
lines are dropped: a `П'…'` constant cannot hold the newline that would end
them. Three BEMSH limits shape the cards:
- the text must end by column 63 («СИМВОЛОВ >63»), so a card holds at most
  8 words;
- `?` and `\` end the card, and BEMSH drops the rest of the text without an
  error. A word with either character is written as `КОНД`, with 0 in
  their places and their codes added by shifts:
  `КОНД П'Q0QW0W'М32В'136'М8В'175'` is `Q?QW\W`;
- `'` is written doubled.

## Limitations

- No double-cell or floating-point words, and no `KEY`.
- `U.` is correct only for values below 2⁴⁰.
- In interpret mode, `S"` returns a pointer into the source line.
- `ABORT"`, `."`, `[CHAR]` and `[']` are compile-only.
- No return-stack overflow check. M12 grows from 074000 and wraps from
  077777 into page 0. So recursion deeper than about 4000 levels overwrites
  the kernel without any message.
- The `тел` run deck uses no Э71 status query; the interpreter assumes a
  terminal.

## History: Форт-БЭСМ-6 (1984)

A Forth for the BESM-6 already existed. The main source is the survey of
Soviet Forth systems in С. Н. Баранов, Н. Р. Ноздрунов, «Язык Форт и его
реализации» (Л.: Машиностроение, 1988), p. 154
([scan](https://ia803109.us.archive.org/20/items/Baranov.Forth.language.and.its.implementation/Baranov.Forth.language.and.its.implementation.pdf)):

> **Форт-БЭСМ-6.** Система разработана в Институте теоретической астрономии
> (ИТА) АН СССР И. Р. Агамирзяном для ЭВМ БЭСМ-6. Используется с 1984 г.
> Работает под управлением ОС ДИСПАК и имеет интерфейс с файловой системой
> КРАБ. Общий объем — 24 К байт (500 слов). По входному языку система ближе
> всего к стандарту «Фиг-форт», вместе с тем используется ряд слов из
> стандарта «Форт-83». Сравнительно большой объем памяти связан с отсутствием
> в ЭВМ БЭСМ-6 байтовой адресации. Для представления стандартного
> двухбайтного значения используется шестибайтное машинное слово БЭСМ-6. По
> той же причине для работы с байтовыми значениями вместо слов C@, C! и
> других введен ряд специальных слов. Из-за особенностей системы команд в
> реализации применен подпрограммный шитый код. Это позволяет включать
> ассемблерные вставки непосредственно в шитый код и наоборот —
> высокоуровневые слова как обращения к подпрограммам внутрь ассемблерных
> определений. Прототипом для встроенного ассемблера является ассемблер
> МАДЛЕН БЭСМ-6. В качестве текстового редактора используется стандартный
> редактор операционной системы.

In short: it was written by I. R. Agamirzyan at the Institute of Theoretical
Astronomy and used from 1984 under ДИСПАК, with an interface to the КРАБ file
system. It had about 500 words, fig-Forth with some Forth-83 words, and
special words for bytes. It used subroutine threading and had a Madlen-style
built-in assembler.

The same book (table 2.1, p. 73) shows the built-in assembler's postfix
notation:

| Madlen | Форт-БЭСМ-6 |
|---|---|
| `, UTC, =15` | `0 0 5 # # UTC,` |
| `, XTA,` | `0 0 XTA,` |
| `3, UTC, 777` | `3 777 UTC,` |

This implementation was written independently of that system. It shares two
design choices with it: subroutine threading and separate handling of bytes.

**Other sources.**
- The survey «Язык Форт в СССР и России» (SoRuCom-2011,
  [computer-museum.ru](https://www.computer-museum.ru/histsoft/fortran_sorucom_2011.htm))
  lists Форт-БЭСМ-6 with the initials «И. А.», apparently a typo. It
  credits «И. Р. Агамирзян» for Астро-Форт for the IBM PC.
- Biography:
  [Wikipedia](https://ru.wikipedia.org/wiki/%D0%90%D0%B3%D0%B0%D0%BC%D0%B8%D1%80%D0%B7%D1%8F%D0%BD,_%D0%98%D0%B3%D0%BE%D1%80%D1%8C_%D0%A0%D1%83%D0%B1%D0%B5%D0%BD%D0%BE%D0%B2%D0%B8%D1%87).
  He graduated from the LSU Faculty of Mathematics and Mechanics in 1979 and
  worked at ИТА АН СССР in 1979–1988.
- No sources or vocabulary listing of Форт-БЭСМ-6 have been found. The book's
  bibliography has no entry for it.
