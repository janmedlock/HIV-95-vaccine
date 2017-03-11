# Do nothing by default.
NULL:

github:
	git subtree push -P src github github

sim_data.tar.xz:
	tar -c -v -f $@ -I 'pixz -9' -C src --exclude-ignore=archive_exclude \
		sim_data
