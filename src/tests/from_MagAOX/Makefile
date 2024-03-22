########################################################################
### Hide commands
AT=@
# TODO use generated_tests/*_tests.cpp eventually.
# do this until all files are working.
GEN_TEST_FILES = \
generated_tests/config_log_generated_tests.cpp \
generated_tests/git_state_generated_tests.cpp \
generated_tests/indidriver_start_generated_tests.cpp \
generated_tests/indidriver_stop_generated_tests.cpp \
generated_tests/loop_closed_generated_tests.cpp \
generated_tests/loop_open_generated_tests.cpp \
generated_tests/loop_paused_generated_tests.cpp \
generated_tests/observer_generated_tests.cpp \
generated_tests/ocam_temps_generated_tests.cpp \
generated_tests/outlet_channel_state_generated_tests.cpp \
generated_tests/outlet_state_generated_tests.cpp \
generated_tests/pico_channel_generated_tests.cpp \
generated_tests/saving_start_generated_tests.cpp \
generated_tests/saving_stop_generated_tests.cpp \
generated_tests/state_change_generated_tests.cpp \
generated_tests/telem_blockgains_generated_tests.cpp \
generated_tests/telem_chrony_stats_generated_tests.cpp \
generated_tests/telem_chrony_status_generated_tests.cpp \
generated_tests/telem_cooler_generated_tests.cpp \
generated_tests/telem_coreloads_generated_tests.cpp \
generated_tests/telem_coretemps_generated_tests.cpp \
generated_tests/telem_dmspeck_generated_tests.cpp \
generated_tests/telem_dmmodes_generated_tests.cpp \
generated_tests/telem_drivetemps_generated_tests.cpp \
generated_tests/telem_fgtimings_generated_tests.cpp \
generated_tests/telem_loopgain_generated_tests.cpp \
generated_tests/telem_observer_generated_tests.cpp \
generated_tests/telem_pico_generated_tests.cpp \
generated_tests/telem_rhusb_generated_tests.cpp \
generated_tests/telem_saving_generated_tests.cpp \
generated_tests/telem_saving_state_generated_tests.cpp \
generated_tests/telem_stage_generated_tests.cpp \
generated_tests/telem_telcat_generated_tests.cpp \
generated_tests/telem_teldata_generated_tests.cpp \
generated_tests/telem_telenv_generated_tests.cpp \
generated_tests/telem_telpos_generated_tests.cpp \
generated_tests/telem_telsee_generated_tests.cpp \
generated_tests/telem_telvane_generated_tests.cpp \
generated_tests/telem_temps_generated_tests.cpp \
generated_tests/telem_usage_generated_tests.cpp \
generated_tests/telem_zaber_generated_tests.cpp \
generated_tests/text_log_generated_tests.cpp \
generated_tests/ttmmod_params_generated_tests.cpp \
generated_tests/user_log_generated_tests.cpp



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
