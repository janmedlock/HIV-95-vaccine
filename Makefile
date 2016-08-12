all: html

html:
	pandoc -s -o README.html -f commonmark README.md
