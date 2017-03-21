all: html test

README.html: README.md
	pandoc -s -o README.html -f commonmark README.md

.PHONY: docs
docs:
	cd docs && $(MAKE) html

.PHONY: html
html: README.html docs

.PHONY: test
test:
	python3 -m unittest model.test

BTURL := https://ir.library.oregonstate.edu/xmlui/bitstream/handle/1957/60549/sim_data.torrent?sequence=1

sim_data.tar.xz:
	btdownloadheadless --saveas $@ $(BTURL)

# Try to use ionice & nice if available.
NICE := $(if $(shell which ionice),ionice -n 7)
NICE += $(if $(shell which nice),nice -n 19)

TARFLAGS := -v
# Try to use pixz (parallel indexing xz) if available.
TARFLAGS += $(if $(shell which pixz),-I pixz)

# sim_data.tar.xz:
# 	$(NICE) tar $(TARFLAGS) -c -f $@ --exclude-ignore=archive_exclude sim_data

# Target samples.pkl files as a concrete file
# that is present in the tar archive.
# This will prevent overwriting existing data.
# If you are having trouble with the data not downloading,
# deleting (or moving/renaming) sim_data/samples.pkl may get it working.
sim_data/samples.pkl: sim_data.tar.xz
	$(NICE) tar $(TARFLAGS) -x -f $<

# Simple name for target to extract data.
sim_data: sim_data/samples.pkl
