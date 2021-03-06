# HIV-95-Vaccine

## HIV model with UNAIDS 90–90–90 & 95–95–95 and vaccine

### Simulation data

**[Jan Medlock](http://people.oregonstate.edu/~medlockj/)
[\<jan.medlock@oregonstate.edu\>](mailto:jan.medlock@oregonstate.edu),
Abhishek Pandey, Alyssa S. Parpia, Amber Tang, Laura A. Skrip,
Alison P. Galvani.
[The Center for Infectious Disease Modeling and Analysis](http://cidma.yale.edu/).**

**Copyright 2015–2017, Jan Medlock et al.  All rights reserved.
Released under the [CC0 1.0 Universal License](LICENSE).**

This is simulation data generated by
[HIV-95-Vaccine](https://github.com/janmedlock/HIV-95-vaccine/)
for 127 countries and aggregated globally and into 9 world regions, as
appears in the paper
> Medlock J, Pandey A, Parpia AS, Tang A, Skrip LA, Galvani
> AP. Effectiveness of UNAIDS targets and HIV vaccination across 127
> countries. *Proc Natl Acad Sci USA*. 2017.
> [doi:10.1073/pnas.1620788114](https://doi.org/10.1073/pnas.1620788114).

In this paper, we estimated the global and country-specific impacts of
UNAIDS 90–90–90 and 95–95–95 targets for HIV diagnosis and treatment, and
of the development of a partially efficacious HIV vaccine.

In addition to generating the data, the
[HIV-95-Vaccine](https://github.com/janmedlock/HIV-95-vaccine/)
code has scripts to load this data, make plots, etc.

The simulation data is stored in Python
[pickle](https://docs.python.org/3.5/library/pickle.html) files
(version 4) generated by
[joblib.dump()](https://pythonhosted.org/joblib/persistence.html).
They can be loaded by
[joblib.load()](https://pythonhosted.org/joblib/persistence.html).

In the top-level directory is `samples.pkl`, which contains a 1000×8
array of the 1000 samples of each of the 8 parameter uncertainty
distributions that were used in running the simulations.

(A cache of the parameter data, `data_sheet.pkl`, will also appear in
the top-level directory if you run any of the
[HIV-95-Vaccine](https://github.com/janmedlock/HIV-95-vaccine/)
tools.)

Each sub-directory is simulation data by country or region.  Inside
each of these are files that store the simulation data by the
treatment target and vaccination program used in the simulation.  The
first part of the filename, before the `+` sign, if any, is the
treatment target used:
* `Status Quo` keeps the 2015 diagnosis, treatment, and
  viral-suppression rates constant through 2035.
* `90–90–90` linearly increases the diagnosis, treatment, and
  viral-suppression rates from their 2015 values each to 90% at the
  beginning of 2020, and then constant to 2035.  (If any rate is above
  90% in 2015, it is kept constant at this level through 2035
  instead.)
* `95–95–95` follows `90–90–90` to 2020 and then the rates each rise
  linearly to 95% at the beginning of 2030, and then constant to
  2035.  (If any rate is above 95% in 2015, it is kept constant at
  this level through 2035 instead.)

If there is no `+` in the filename, no vaccination was used in the
simulation.  Otherwise, following the `+` is a description of the
characteristics of the vaccination program.  Finally, the filename may
end in `-mode.pkl`, in which case it was generated using the modes of
the parameter uncertainty distributions, or simply `.pkl`, in which
case it was generated using the 1000 samples of the parameter
uncertainty distributions (from `samples.pkl`).

The files of the simulation data using the samples from the parameter
uncertainty distributions each contain a 1000×2401×10 array, where the
first dimension is over the samples, the second dimension is over time
(the beginning of 2015 to the beginning of 2035, with 120 points per
year), and the third dimension is over the model variables (see
below).  The files of the simulation data using the modes of the
parameter uncertainty distributions each contain a 2401×10 array,
where the first dimension is over time and the second dimension is
over the model variables.  The model variables are, in the order in
the stored array:
1. The number of susceptible people.
2. The number of vaccinated people.
3. The number of acutely infected people.
4. The number of chronically infected people who are undiagnosed.
5. The number of chronically infected people who are diagnosed but
   untreated.
6. The number of chronically infected people who are treated but not
   virally suppressed.
7. The number of chronically infected people who are virally suppressed.
8. The number of people with AIDS.
9. The cumulative number of AIDS deaths since 2015.
10. The cumulative number of new HIV infections since 2015.

From these, our tools in
[HIV-95-Vaccine](https://github.com/janmedlock/HIV-95-vaccine/)
compute standard summaries such as prevalence over time and calculate
statistics such as median and quantiles over the sample runs.

Please see the documentation to
[HIV-95-Vaccine](https://github.com/janmedlock/HIV-95-vaccine/)
for more.
