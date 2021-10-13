#!/usr/bin/env sh

PATH="$(cd "$(dirname $0)/.." && pwd)/src:$PATH"

testUsage() {
    true
    # assertFalse wordpaper
    # assertContains "$( || true)" Usage
}

. shunit2
