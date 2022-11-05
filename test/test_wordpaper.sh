#!/usr/bin/env sh

BASE_DIR="$(cd "$(dirname $0)/.." && pwd)"
PATH="$BASE_DIR/src:$PATH"

setUp() {
    export CACHE_DIR="$BASE_DIR/test/fixtures/cache"
    export OUTPUT_DIR="$SHUNIT_TMPDIR/output"
}

tearDown() {
    if [[ -d $OUTPUT_DIR ]]; then
        rm -rf "$OUTPUT_DIR"
    fi
}

testSuccess() {
    cat <<EOS | wordpaper --cache-dir "$CACHE_DIR" --output-dir "$OUTPUT_DIR"
good, ona
EOS
    assertTrue "[[ -f $OUTPUT_DIR/754a9714-good.jpeg ]]"
	assertTrue "[[ -f $OUTPUT_DIR/63f37d32-good.jpeg ]]"
	assertTrue "[[ -f $OUTPUT_DIR/bb0dbd4b-good.jpeg ]]"
	assertTrue "[[ -f $OUTPUT_DIR/f3467553-good.jpeg ]]"
	assertTrue "[[ -f $OUTPUT_DIR/e6d720cb-good.jpeg ]]"
	assertTrue "[[ -f $OUTPUT_DIR/48240959-good.jpeg ]]"
	assertTrue "[[ -f $OUTPUT_DIR/6756816d-good.jpeg ]]"
	assertTrue "[[ -f $OUTPUT_DIR/f27d318a-good.jpeg ]]"
	assertTrue "[[ -f $OUTPUT_DIR/a42d15ca-good.jpeg ]]"
	assertTrue "[[ -f $OUTPUT_DIR/ff0a7a14-good.jpeg ]]"
}


testEmptyLine() {
    cat <<EOS | wordpaper --cache-dir "$CACHE_DIR" --output-dir "$OUTPUT_DIR"

EOS
}

testCommentLine() {
    cat <<EOS | wordpaper --cache-dir "$CACHE_DIR" --output-dir "$OUTPUT_DIR"
# this is
# comment
EOS
}

. shunit2
