# Replace these targets with the repo's real commands. CI and agents call them.
.PHONY: setup lint test dev
setup:
	@echo "no setup yet"
lint:
	@find . -name '*.sh' -not -path './.git/*' -exec sh -c 'for f; do bash -n "$$f" || exit 1; done' _ {} +
	@find . -name '*.py' -not -path './.git/*' -exec python3 -m py_compile {} +
test:
	@python3 -m unittest discover -s tests -t . -v
dev:
	@echo "nothing to run"
