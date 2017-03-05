# HIV-95-vaccine

## HIV model with UNAIDS 90-90-90 & 95-95-95 and vaccine

**[Jan Medlock](http://people.oregonstate.edu/~medlockj/)
[\<jan.medlock@oregonstate.edu\>](mailto:jan.medlock@oregonstate.edu),
Abhishek Pandey, Alyssa S. Parpia, Amber Tang, Laura A. Skrip,
Alison P. Galvani.
[The Center for Infectious Disease Modeling and Analysis](http://cidma.yale.edu/).**

**Copyright 2015–2016, Jan Medlock et al.  All rights reserved.
Released under the [GNU AGPL 3](LICENSE).**

This repository contains Python code and data used to simulate and
analyze HIV transmission in many (127, as of this writing) countries
around the world.
<!---
Add link to paper here.
--->

The scripts and model code are entirely written in Python3, using many
third-party libraries.  Most notably:
[Python3](http://www.python.org/),
[NumPy & SciPy](http://www.scipy.org/),
[matplotlib](http://matplotlib.org/),
[pandas](http://pandas.pydata.org/),
[cartopy](http://scitools.org.uk/cartopy/),
[Seaborn](https://stanford.edu/~mwaskom/software/seaborn/),
& [Sphinx](http://www.sphinx-doc.org/).
See [module_versions.txt](module_versions.txt) for a full list: note
that many of the modules listed there are dependencies of the modules
listed above.

### Documentation

The full development documentation can be built using
[Sphinx](http://www.sphinx-doc.org/).  `make html` (using
[GNU make](https://www.gnu.org/software/make/) or similar) in either
the root or [docs/](docs/) directories will build the documentation,
which will then be in *docs/_build/html/*.  The scripts, modules,
etc. mentioned below are covered in this documentation.

### Parameter data

* [data_sources/](data_sources/) contains the data used to
  parametrize the model and references to the sources of these data.

* [data_sheet.xlsx](data_sheet.xlsx) contains a hand-curated version
  of [data_sources/](data_sources/), with fewer references to sources
  etc, that is parsed by the simulation code.

* [data_sheet_report.py](data_sheet_report.py) reports on the
  completeness of the data in [data_sheet.xlsx](data_sheet.xlsx).

### Simulations

* [run_modes.py](run_modes.py) runs simulations using the modal
  parameter values.  This is fairly fast, tens of seconds for each
  country-target combination, approximately 10 cpu-hours for 127
  countries and 6 targets.  The result will be in *results/modes.h5*,
  which is around 200MB for 127 countries and 6 targets.

* [run_vaccine_scenarios.py](run_vaccine_scenarios.py) runs different
  vaccine scenarios using the modal parameter values.  Again, this is
  as fast as [run_modes.py](run_modes.py) per country-target, but has
  7 targets instead of 6, so takes a little bit longer to run.  The
  result will be in *results/vaccine_sensitivity.h5*, which is around
  450MB for 127 countries and 6 targets.

* [run_samples.py](run_samples.py) runs simulations using parameter
  samples.  **This is very slow**: it is only tens of seconds per
  sample-country-target, but the default is 1000 samples, so it takes
  tens of cpu-**days** to run everything.  The data from the runs will
  be in *results/*, under a directory for each country, with a *.pkl*
  file for each target.  **The resulting total data generated for 127
  countries and 6 targets is around 315GB.**

We are currently exploring options for a public archive of the
simulation data we have generated.

### Post-processing

* [build_regionals.py](build_regionals.py) sums the results to built
  results for regions and globally.  These are built in *results/*
  directories for each region, one *.pkl* file for each target.

* [build_percentiles.py](build_percentiles.py) summarizes the median
  and a few percentiles of selected outcomes from the *.pkl* data from
  [runs_samples.py](runs_samples.py) to *results/samples_stats.h5*
  for easier post-processing and plotting.  The resulting file is
  around 1GB for 127 countries and 6 targets.  Run
  [build_regionals.py](build_regionals.py) first to ensure that the
  regional and global results also get converted.

### Plotting

The plotting scripts are in the [plots/](plots/) directory.  They
generally require having run the simulations and post-processing
tools.  A few highlights:
* [effectiveness.py](plots/effectiveness.py) uses data generated by
  [run_samples.py](run_samples.py) (and post-processed with
  [build_regionals.py](build_regionals.py) &
  [build_percentiles.py](build_percentiles.py)) to make two sets of
  files:
  + *effectiveness.pdf* & *effectiveness.png* are graphs of selected
    outcomes globally and for a few selected countries.
  + *effectiveness_all.pdf* are graphs of selected outcomes for all
    regions and countries.  **This part is a bit slow, maybe a few
    minutes.**  You may want to comment out `plot_all()` to avoid
    running this part.

* [effectiveness_modes.py](plots/effectiveness_modes.py) uses data
  generated by [run_modes.py](run_modes.py) to make graphs of selected
  outcomes globally and for a few selected countries.

* [vaccine_sensitivity.py](plots/vaccine_sensitivity.py) uses data
  generated by [run_vaccine_scenarios.py](run_vaccine_scenarios.py) to
  make graphs of selected outcomes globally and for a few selected
  countries.

* [initial_prevalence_map.py](plots/initial_prevalence_map.py) uses
  the data in [data_sheet.xlsx](data_sheet.xlsx) to make a choropleth
  map of 2015 prevalence.  **No simulation data is needed.**

* [transmission_rate.py](plots/transmission_rate.py) uses the data
  in [data_sheet.xlsx](data_sheet.xlsx) to make a graph of estimated
  transmission rates for each country.  **No simulation data is
  needed.**

* [infections_averted_map.py](plots/infections_averted_map.py) uses
  data generated by [run_samples.py](run_samples.py) (and
  post-processed with [build_regionals.py](build_regionals.py) &
  [build_percentiles.py](build_percentiles.py)) to make choropleth
  maps infections averted for selected targets.

* [infections_per_capita_averted_map.py](plots/infections_per_capita_averted_map.py)
  uses data generated by [run_samples.py](run_samples.py) (and
  post-processed with [build_regionals.py](build_regionals.py)) to
  make choropleth maps infections per capita averted for selected
  targets.  **This is very slow—of minutes—and we haven't found the
  resulting maps useful.**

Note that the post-processing of PDF files uses `pdftocairo` from
[Poppler](https://poppler.freedesktop.org/) (in `pdfoptimize()` in
[plots/common.py](plots/common.py)) to reduce the size of the PDF
files and [PDFtk](https://www.pdflabs.com/tools/pdftk-server/) (in
`pdf_add_info()` in [plots/common.py](plots/common.py)) to add
metadata.  Neither of these is necessary and can be commented out.

### Simulation code

The simulation code is in [model/](model/).  A few development test
scripts are in [tests/](tests/).  See the development documentation
in for more information.

### Miscellany

[module_versions.txt](module_versions.txt) lists the library
versions that were used in running this
code.  [module_versions.py](module_versions.py) is used to generate
this list.  (Note: running [module_versions.py](module_versions.py) will
overwrite [module_versions.txt](module_versions.txt) with the versions
on your computer, losing information about what is on my computer.
This may not be what you want to do.)
