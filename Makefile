# Do nothing by default.
NULL:

github:
	git subtree push -P src github github

sim_data.tar.xz:
	ionice -n 7 nice -n 19 \
		tar -c -v -f $@ -I 'pixz -6' -C src \
			--exclude-ignore=archive_exclude sim_data
