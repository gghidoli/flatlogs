
AT=@

all: generated/binarySchemata.inc do_test

do_tests: generated/binarySchemata.inc do_tests.cpp
	$(AT)g++  -I. -I../../../include/ do_tests.cpp -o $@

do_test: do_tests
	$(AT)./do_tests

clean:
	$(AT)$(RM) -R "./types/generated/" "./generated/" ./do_tests Schemata_test

### todo: remove checksum testing of generated/* and types/generated/*
generated/binarySchemata.inc: types/*.hpp types/schemas/*.fbs
	$(AT)$(RM) -R "./types/generated/" "./generated/"
	$(AT)../../flatlogcodes 2>/dev/null
	$(AT)cd types/generated; for bfb in *.bfbs; do xxd -i $$bfb > $$(basename $$bfb).h; done
	$(AT)cat types/generated/*.bfbs.h > $@
	$(AT)md5sum types/generated/* generated/* | md5sum | grep -q '^2d661103acb5d77b8bc96cadf30b5a95 ' || $(RM) $@
	$(AT)echo Success
