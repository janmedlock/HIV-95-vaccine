all: diagram_standalone.pdf diagram_standalone.png \
	supporting_information.pdf cover_letter.pdf figs.pdf


diagram_standalone.pdf:	diagram_standalone.tex diagram.tex
	pdflatex $<

diagram_standalone.png:	diagram_standalone.pdf
	convert -density 600 $< $@

supporting_information.pdf:	supporting_information.tex
	pdflatex $<
	biber $<
	pdflatex $<
	pdflatex $<

cover_letter.pdf:	cover_letter.tex
	pdflatex $<

figs.pdf:	figs.tex
	pdflatex $<
