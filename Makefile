# Do nothing by default.
NULL:

github:
	git subtree push -P src github github

sim_data.tar.xz:
	tar cf $@ -v -I 'pixz -9' -C src --exclude-ignore=archive_exclude \
		sim_data
