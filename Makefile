# Replace these targets with the repo's real commands. CI and agents call them.
.PHONY: setup lint test dev
setup:
	@echo "no setup yet"
lint:
	@find . -name '*.sh' -not -path './.git/*' -exec bash -n {} \;
	@find . -name '*.py' -not -path './.git/*' -exec python3 -m py_compile {} +
test:
	@echo "no tests yet"
dev:
	@echo "nothing to run"
