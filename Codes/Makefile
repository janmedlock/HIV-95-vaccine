all: html test

html:
	cd docs && $(MAKE) html

test:
	python3 -m unittest model.test
