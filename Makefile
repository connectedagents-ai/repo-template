# Replace these targets with the repo's real commands. CI and agents call them.
.PHONY: setup lint test dev
setup:
	@echo "no setup yet"
lint:
	@find . -name '*.sh' -not -path './.git/*' -print0 | xargs -0 -r -n1 bash -n
	@find . -name '*.py' -not -path './.git/*' -print0 | xargs -0 -r python3 -m py_compile
test:
	@echo "no tests yet"
dev:
	@echo "nothing to run"
