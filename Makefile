dev:
	while true; \
	do find src test -type f | entr -cdr src/wordpaper; \
	(( $$? == 0 || $$? > 128 )) && exit 0; \
	done
.PHONY: dev

test:
	while true; \
	do find src test -type f | entr -cdr test/test_wordpaper.sh; \
	(( $$? == 0 || $$? > 128 )) && exit 0; \
	done
.PHONY: test
	
install:
	nix-env -f ./. -i wordpaper
.PHONY: install
