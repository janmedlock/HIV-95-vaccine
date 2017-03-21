# Do nothing by default.
.PHONY: NULL
NULL:

.PHONY: github
github:
	git subtree push -P src github github
