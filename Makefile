all: html test

html:
	pandoc -s -o README.html -f commonmark README.md
	cd docs && $(MAKE) html

test:
	python3 -m unittest model.test
