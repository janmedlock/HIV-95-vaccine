# Do nothing by default.
NULL:

github:
	git subtree push -P src github github

sim_data.tar:
	tar cf $@ -v -C src --exclude-ignore=archive_exclude sim_data
