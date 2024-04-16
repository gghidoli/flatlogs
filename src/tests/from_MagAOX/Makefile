########################################################################
### Hide commands
AT=@
GEN_TEST_FILES = generated_tests/*_generated_tests.cpp

# STILL TODO
# generated_tests/telem_fxngen_generated_tests.cpp \
# generated_tests/telem_stdcam_generated_tests.cpp \
# generated_tests/software_log_generated_tests.cpp


########################################################################
### Generate code, run tests
all: generated/binarySchemata.inc do_catch2_test do_test

########################################################################
### Generate code and flatbuffer binary schema from text schemas (*.fbs)
generated/binarySchemata.inc: types/*.hpp types/schemas/*.fbs
	$(AT)$(RM) -R "./types/generated/" "./generated/"
	$(AT)../../flatlogcodes 2>/dev/null
	$(AT)cd types/generated; for bfb in *.bfbs; do xxd -i $$bfb > $$(basename $$bfb).h; done
	$(AT)cat types/generated/*.bfbs.h > $@

########################################################################
### Build and run Catch2 tests
generated_tests: $(GEN_TEST_FILES)

$(GEN_TEST_FILES) :
	python3 generateTemplatedCatch2Tests.py

catch2_tests: generated/binarySchemata.inc $(GEN_TEST_FILES) catch2_tests.cpp
	$(AT)g++ -std=c++14 -I. -I../../../include $(GEN_TEST_FILES) catch2_tests.cpp -o $@

do_catch2_test: catch2_tests
	$(AT)./catch2_tests

########################################################################
### Build and run non-Catch2 test (will probably remove at some point)
do_tests: generated/binarySchemata.inc do_tests.cpp
	$(AT)g++ -std=c++11 -I. -I../../../include/ do_tests.cpp -o $@

do_test: do_tests
	$(AT)./do_tests

########################################################################
clean:
	$(AT)$(RM) -R "./types/generated/" "./generated/" "./generated_tests/" ./do_tests Schemata_test catch2_tests
