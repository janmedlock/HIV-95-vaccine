all: diagram_standalone.pdf diagram_standalone.png supplementary_text.pdf \
	cover_letter.pdf


diagram_standalone.pdf:	diagram_standalone.tex diagram.tex
	pdflatex $<

diagram_standalone.png:	diagram_standalone.pdf
	convert -density 600 $< $@

supplementary_text.pdf:	supplementary_text.tex
	pdflatex $<
	biber $<
	pdflatex $<
	pdflatex $<

cover_letter.pdf:	cover_letter.tex
	pdflatex $<
