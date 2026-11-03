#!/bin/sh
# Run each tests/NAME.fs through FORTH under dispak and compare the terminal
# output (BOM removed) with tests/NAME.out.  Usage: tests/run.sh [NAME ...]
# Set UPDATE=1 to rewrite the .out files from the current output.
cd "$(dirname "$0")/.." || exit 1
fail=0
[ $# -eq 0 ] && set -- $(ls tests/*.fs | sed 's,tests/,,;s,\.fs$,,')
for t in "$@"; do
    out=build/test-$t.out
    timeout 60 tools/run-dispak.sh -l build/forth.b6 < tests/$t.fs \
        | sed '1s/^\xEF\xBB\xBF//' > $out
    if [ -n "$UPDATE" ]; then
        cp $out tests/$t.out
    elif diff -u tests/$t.out $out; then
        echo "PASS $t"
    else
        echo "FAIL $t"; fail=1
    fi
done
exit $fail
