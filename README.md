# HIV-95-vaccine

## HIV model with UNAIDS 90–90–90 & 95–95–95 and vaccine

**[Jan Medlock](http://people.oregonstate.edu/~medlockj/)
[\<jan.medlock@oregonstate.edu\>](mailto:jan.medlock@oregonstate.edu),
Abhishek Pandey, Alyssa S. Parpia, Amber Tang, Laura A. Skrip,
Alison P. Galvani.
[The Center for Infectious Disease Modeling and Analysis](http://cidma.yale.edu/).**

**Copyright 2015–2017, Jan Medlock et al.  All rights reserved.
Released under the [GNU AGPL 3](LICENSE).**

This repository contains Python code and data used to simulate and
analyze HIV transmission in 127 countries around the world.
> Medlock J, Pandey A, Parpia AS, Tang A, Skrip LA, Galvani
> AP. Effectiveness of UNAIDS targets and HIV vaccination across 127
> countries. *Proc Natl Acad Sci USA*. 2017.
> [doi:10.1073/pnas.1620788114](https://doi.org/10.1073/pnas.1620788114).

The scripts and model code are entirely written in Python3, using many
third-party libraries.  Most notably:
[Python3](http://www.python.org/),
[NumPy & SciPy](http://www.scipy.org/),
[matplotlib](http://matplotlib.org/),
[pandas](http://pandas.pydata.org/),
[cartopy](http://scitools.org.uk/cartopy/),
[Seaborn](https://seaborn.pydata.org/),
& [Sphinx](http://www.sphinx-doc.org/).
See [module_versions.txt](module_versions.txt) for a full list: note
that many of the modules listed there are dependencies of the modules
listed above.

### Documentation

The full development documentation can be built using
[Sphinx](http://www.sphinx-doc.org/).  `make html` (using [GNU
make](https://www.gnu.org/software/make/) or similar) in either the
root or `docs` directories will build the documentation, which will
then be in `docs/_build/html` (also accessible with the symlink
`docs/html`).  The scripts, modules, etc. mentioned below are covered
in this documentation.

### Parameter data

* [data_sources](data_sources) contains the data used to
  parametrize the model and references to the sources of these data.

* [data_sheet.xlsx](data_sheet.xlsx) contains a hand-curated version
  of [data_sources](data_sources), with fewer references to sources
  etc., that is parsed by the simulation code.

* [data_sheet_report.py](data_sheet_report.py) reports on the
  completeness of the data in [data_sheet.xlsx](data_sheet.xlsx).

### Simulations

Listed below are scripts to generate the simulation data: running them
requires **tens of cpu-days**.

Alternatively, running `make sim_data` in the root directory will
automatically download and extract the all of the simulation data
(about **150GB**) from
[https://hdl.handle.net/1957/60549](https://hdl.handle.net/1957/60549).
If that link is broken, try
[doi:10.5072/FK20005Q3C](https://doi.org/10.5072/FK20005Q3C).

* [run_modes.py](run_modes.py) runs simulations using the modal
  parameter values.  This is fairly fast, tens of seconds for each
  country-target combination, approximately 10 cpu-hours for 127
  countries and 6 targets.  The resulting data will be in `sim_data`,
  under a directory for each country, with a `-mode.pkl` file for each
  target.  The resulting total data generated for 127 countries and 6
  targets is around 151MB.

* [run_vaccine_scenarios.py](run_vaccine_scenarios.py) runs different
  vaccine scenarios using the modal parameter values.  This is about
  as fast as [run_modes.py](run_modes.py).  The resulting data will be
  in `sim_data`, under a directory for each country, with a
  `-mode.pkl` file for each target.  The resulting total data
  generated for 127 countries and 6 targets is around 151MB.

* [run_samples.py](run_samples.py) runs simulations using parameter
  samples.  **This is very slow**: it is only tens of seconds per
  sample-country-target, but the default is 1000 samples, so it takes
  tens of cpu-**days** to run everything.  The data from the runs will
  be in `sim_data`, under a directory for each country, with a `.pkl`
  file for each target.  **The resulting total data generated for 127
  countries and 6 targets is around 147GB.**

### Plotting

The plotting scripts are in the [plots](plots) directory.  They
require having run the simulations unless otherwise noted.  A few highlights:
* [effectiveness.py](plots/effectiveness.py) makes graphs of selected
  outcomes globally and for a few selected countries.

* [effectiveness_regions.py](plots/effectiveness_regions.py) makes graphs of
  selected outcomes by region.

* [vaccine_sensitivity.py](plots/vaccine_sensitivity.py) makes graphs
  of selected outcomes globally and for a few selected countries.

* [initial_prevalence_map.py](plots/initial_prevalence_map.py) makes
  a choropleth map of 2015 prevalence.  **No simulation data is needed.**

* [infections_averted_map.py](plots/infections_averted_map.py) makes
  choropleth maps infections averted for selected targets.

* [transmission_rate.py](plots/transmission_rate.py) makes a graph of
  estimated transmission rates for each country.  **No simulation data is
  needed.**

### Simulation code

The simulation code is in [model](model).  A few development test
scripts are in [tests](tests).  See the development documentation
in for more information.

### Miscellany

[module_versions.txt](module_versions.txt) lists the library
versions that were used in running this
code.  [module_versions.py](module_versions.py) is used to generate
this list.  (Note: running [module_versions.py](module_versions.py) will
overwrite [module_versions.txt](module_versions.txt) with the versions
on your computer, losing information about what is on my computer.
This may not be what you want to do.)
