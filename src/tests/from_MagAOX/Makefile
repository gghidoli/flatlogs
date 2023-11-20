
test:
	@$(RM) -R "./types/generated/" "./generated/"
	@../../flatlogcodes 2>/dev/null
	@md5sum types/generated/* generated/* | md5sum | grep -q '^dd26385b5bcb3b02ae81e08d03db1b50 '
	@echo Success
	@$(RM) -R "./types/generated/" "./generated/"
