# FORTH for BESM-6.  See README.md.
#   make          assemble forth.be + lib/core.fs with BEMSH, write the image
#   make run      interactive session (Latin output)
#   make test     run tests/*.fs and compare with tests/*.out
#   make dialog   scripted interactive session on a pty (needs expect)
#   make probe    the Э71/memory/Э75 probe in probe/probe.be
PYTHON ?= python3
.DELETE_ON_ERROR:
GEN := build/forth-gen.be

all: build/forth.b6

$(GEN): forth.be lib/core.fs tools/mkforth.py tools/gost.py
	mkdir -p build
	$(PYTHON) tools/mkforth.py forth.be lib/core.fs > $@

build/forth.b6: $(GEN) tools/build.py tools/chkprelude.py
	$(PYTHON) tools/build.py --name forth --limit 4000 $(GEN)
	$(PYTHON) tools/chkprelude.py build/forth.lst lib/core.fs

run: build/forth.b6
	tools/run-dispak.sh -l build/forth.b6

test: build/forth.b6
	tests/run.sh

dialog: build/forth.b6
	timeout 60 tools/dialog.expect

probe:
	$(PYTHON) tools/build.py --name probe probe/probe.be
	echo 'abc 123' | timeout 20 tools/run-dispak.sh -l build/probe.b6

clean:
	rm -rf build

.PHONY: all run test dialog probe clean
