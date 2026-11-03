# Working notes

FORTH for the BESM-6 under dispak.  See README.md for usage and design.

## Build and check

- `make` regenerates `build/forth-gen.be` (tools/mkforth.py), assembles it
  with BEMSH and writes the run deck.  `make test` must pass after every
  change; refresh expectations with `UPDATE=1 tests/run.sh NAME` only after
  checking the new output by hand.
- Always run dispak through `tools/run-dispak.sh` (isolated HOME) and wrap
  runs in `timeout`.
- The listing is `build/forth.lst`; look there for encodings and addresses.

## BEMSH pitfalls (ИПМ МАКРО-БЕМШ 06/78)

- Register names come from the library macro `М` (card `ЧТКОМП420070` plus
  `М` after `СТАРТ`).  Registers are octal: `М1`–`М7`, `М10`–`М17`; there is
  no `М8`/`М9`.  Names work in any field (`СЧИМ М13`, `УИИ М7(М5)`).
- Bare numbers are decimal (`СДА 64-8`); octal is `В'17'`, absolute
  addresses `'70000'`.
- A label starts a new word.  `ПВ` and extracodes go to the right half, with
  a `МОДА` filler, which sets C = 0: put a label on any `МОД`/`МОДА`
  that must reach the next `ПВ`.
- Short-address instructions reach only 0–07777 and 070000+: keep all
  variables, constants and tables near the start of the image.
- Cards: BEMSH reads columns 1–64 only and drops the rest without an
  error (tools/build.py rejects longer cards); labels at most six
  characters.
- Text constants `П'…'`: `?` and `\` end the card without any error
  (`tools/chkprelude.py` guards the prelude), and an operand may not pass
  column 63 («СИМВОЛОВ >63»).

## dispak facts relied on

- Э75 stores A as an instruction word; `ЗП` stores data words, and executing
  one stops with «КОНТРОЛЬ КОМАНДЫ».
- `СЧМ` (XTS) computes its address after the push: `СЧМ -2(М17)` is OVER.
- Э71 (non-raw) prints GOST up to 0172/0377; bit 4 of the input opcode
  prints the buffer itself as the prompt, without a line feed.
- `НТР 3` survives Э71.
