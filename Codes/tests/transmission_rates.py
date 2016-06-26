#!/usr/bin/python3
'''
Test the estimation of transmission rates.
'''

import abc
import sys
import warnings

from matplotlib import pyplot
from matplotlib import ticker
from matplotlib.backends import backend_pdf
import numpy
import pandas
from scipy import stats

sys.path.append('../plots')
import common
sys.path.append('..')
import model

# Here because code to suppress warnings is in common.
import seaborn


class Estimator(metaclass = abc.ABCMeta):
    '''
    Abstract base class for transmission-rate estimators.
    '''
    def __init__(self, country):
        self.country = country
        # Read the incidence, prevalence, population, etc from the datasheet.
        self.parameters = model.Parameters(country)
        # Estimate the transmission rates.
        self.transmission_rates = self.estimate()
        # Use them to set up parameter values for R0, simulation, etc.
        self._set_parameter_values()
        # Attach R0 for convenience.
        self.R0 = self.parameter_values.R0

    # Methods decorated with @abc.abstractmethod must be implemented
    # by any subclass of this class.

    @abc.abstractmethod
    def estimate(self):
        '''
        Estimate transmission rates.
        '''

    @abc.abstractmethod
    def set_transmission_rates(self):
        '''
        Set the transmission rates in the .parameters object for future
        use (e.g. in simulation).
        '''

    @abc.abstractmethod
    def plot_estimates(self, ax, **kwargs):
        '''
        Plot the estimates of the transmission rates.
        '''

    def estimate_vs_time(self):
        r'''
        Estimate the transmission rate at each time.

        The per-capita incidence is

        .. math:: i(t) = \lambda(t) \frac{S(t)}{N(t)}
                  = \beta \frac{I(t)}{N(t)} \frac{S(t)}{N(t)},

        assuming no differences in transmission between acute, unsuppressed,
        suppressed and AIDS classes (i.e. :math:`I = A + U + D + V + W`).

        If :math:`p = \frac{I}{N}` is the prevalence,

        .. math:: i(t) = \beta p(t) (1 - p(t)).

        Rearranging gives

        .. math:: \beta(t) = \frac{i(t)}{p(t) (1 - p(t))}.
        '''
        # Interpolate in case of any missing data.
        prevalence = self.parameters.prevalence.interpolate(method = 'index')
        incidence = self.parameters.incidence.interpolate(method = 'index')
        transmission_rates_vs_time = incidence / prevalence / (1 - prevalence)
        # Remove nan entries.
        return transmission_rates_vs_time.dropna()

    def _set_parameter_values(self):
        '''
        Set up the .parameter_values object from the .parameters object,
        and set the transmission rates using our estimates.
        '''
        # Attach .transmission_rates to .parameters,
        # in case they are scipy.stats random variables.
        self.parameters.transmission_rates = self.transmission_rates

        # Convert any scipy.stats in .parameters to values
        # using maximum likelikehood (mode) or by sampling.
        self.parameter_values = self.parameters.mode()
        # self.parameter_values = self.parameters.sample()

        self.set_transmission_rates()

        # Make sure all transmission rates are finite.
        # assert numpy.isfinite(self.parameter_values.transmission_rates).all()
        if not numpy.isfinite(self.parameter_values.transmission_rates).all():
            msg = "{}: country = '{}': Non-finite transmission_rates = {}!"
            warnings.warn(msg.format(self.__class__.__name__,
                                     self.country,
                                     self.parameter_values.transmission_rates))

        # Make sure all transmission rates are non-negative.
        assert not numpy.any(self.parameter_values.transmission_rates < 0)

    def simulate(self):
        '''
        Simulate the model forward in time.
        '''
        results = model.Simulation(self.parameter_values,
                                   'baseline',
                                   run_baseline = False)
        return results

    def plot_transmission_rates(self,
                                ax = None,
                                plot_vs_time = True,
                                title = True,
                                **kwargs):
        '''
        Plot estimates of the transmission rates and, optionally,
        the transmission rates vs time.

        This sets up the plot axes, legend, etc, so that plot_estimates()
        doesn't need to.
        '''
        if ax is None:
            ax = pyplot.gca()

        if plot_vs_time:
            self.plot_transmission_rates_vs_time(ax, **kwargs)

        # The plot_estimates() methods I have written use ax.axhline(),
        # which doesn't automatically use the axes prop_cycler.  So
        # grab the next style from the cycler and pass to
        # plot_estimates().
        style = next(ax._get_lines.prop_cycler)
        kwargs.update(style)
        # Add some alpha.
        kwargs.update(dict(alpha = 0.7))
        self.plot_estimates(ax, **kwargs)

        ax.set_ylabel('Transmission rate (per year)')
        if title:
            ax.set_title(self.country)
        ax.legend(loc = 'upper right', frameon = False)

        return ax

    def plot_transmission_rates_vs_time(self,
                                        ax = None,
                                        **kwargs):
        '''
        Plot the estimate of the transmision rates vs. time.
        '''
        if ax is None:
            ax = pyplot.gca()
        transmission_rates_vs_time = self.estimate_vs_time()
        ax.plot(transmission_rates_vs_time.index,
                transmission_rates_vs_time,
                label = 'estimates at each time',
                marker = '.',
                markersize = 10,
                **kwargs)
        return ax

    def _plot_sim_cell(self, ax, results, stat, plot_data = True):
        '''
        Plot one axes of simulation and historical data figure.
        '''
        percent = False
        if stat == 'infected':
            scale = 1e6
            ylabel = 'Infected\n(M)'
            data = self.parameters.prevalence * self.parameters.population
            t = results.t
            val = results.infected
        elif stat == 'prevalence':
            percent = True
            ylabel = 'Prevelance\n'
            data = self.parameters.prevalence
            t = results.t
            val = results.prevalence
        elif stat == 'incidence':
            scale = 1e-3
            ylabel = 'Incidence\n(per 1000 per y)'
            data = self.parameters.incidence
            # Compute from simulation results.
            t = results.t
            ni = numpy.asarray(results.new_infections)
            n = numpy.asarray(results.alive)
            val = numpy.diff(ni) / numpy.diff(t) / n[..., 1 :]
            # Need to drop one t value since we have differences above.
            t = t[1 : ]
        elif stat == 'drug_coverage':
            percent = True
            ylabel = 'Drug\ncoverage'
            data = self.parameters.drug_coverage
            t = results.t
            on_drugs = numpy.asarray(results.treated
                                     + results.viral_suppression)
            infected = numpy.asarray(results.infected)
            val = on_drugs / infected
        else:
            raise ValueError("Unknown stat '{}'".format(stat))

        if percent:
            scale = 1 / 100

        # Plot historical data.
        data_ = data.dropna()
        if plot_data:
            ax.plot(data_.index, data_ / scale, marker = '.', markersize = 10)

        # Plot simulation data.
        ax.plot(t + 2015, val / scale, alpha = 0.7)

        # Make a dotted line connecting the end of the historical data
        # and the begining of the simulation.
        x = [data_.index[-1], t[0] + 2015]
        y = [data_.iloc[-1], val[0]]
        ax.plot(x, numpy.asarray(y) / scale,
                linestyle = 'dotted', color = 'black')

        ax.set_xlim(1990, t[-1] + 2015)
        ax.grid(True, which = 'both', axis = 'both')
        ax.set_xticks(range(1990, int(t[-1] + 2015), 10))
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
        if percent:
            ax.yaxis.set_major_formatter(common.PercentFormatter())
        ax.set_ylabel(ylabel, size = 'medium')

    def plot(self, fig = None, plot_data = True):
        '''
        Plot transmission rate estimates and compare simulation
        with historical data.
        '''
        results = self.simulate()

        if fig is None:
            fig = pyplot.gcf()
        # Layout is 2 columns,
        # 1 big axes in the left column
        # for plotting transmission rates,
        # and nsubplots axes in the right column for plotting
        # simulation vs historical data.
        nsubplots = 4
        axes = []
        ax = fig.add_subplot(1, 2, 1)
        axes.append(ax)
        for i in range(nsubplots):
            # Use the first axes in this column to share x-axis
            # range, labels, etc.
            sharex = axes[1] if i > 0 else None
            ax = fig.add_subplot(nsubplots, 2, 2 * i + 2, sharex = sharex)
            axes.append(ax)
        # Turn off x-axis labels on non-bottom subplots.
        if nsubplots > 1:
            for ax in axes:
                if not ax.is_last_row():
                    for l in ax.get_xticklabels():
                        l.set_visible(False)
                    ax.xaxis.offsetText.set_visible(False)

        # Set title
        fig.text(0.5, 1, self.country,
                 verticalalignment = 'top',
                 horizontalalignment = 'center')

        self.plot_transmission_rates(axes[0], title = False,
                                     plot_vs_time = plot_data)

        self._plot_sim_cell(axes[1], results, 'infected',
                            plot_data = plot_data)

        self._plot_sim_cell(axes[2], results, 'prevalence',
                            plot_data = plot_data)

        self._plot_sim_cell(axes[3], results, 'incidence',
                            plot_data = plot_data)

        self._plot_sim_cell(axes[4], results, 'drug_coverage',
                            plot_data = plot_data)

        fig.tight_layout()
        return fig


class GeometricMean(Estimator):
    '''
    Estimate the transmission rate at each time,
    then take the geometric mean over time.
    '''
    def estimate(self):
        '''
        Get the estimates of the transmission rate at each time
        and take the geometric mean over time.
        '''
        transmission_rates_vs_time = self.estimate_vs_time()
        return stats.gmean(transmission_rates_vs_time)

    def set_transmission_rates(self):
        '''
        Scale parameters.transmission_rate_* by the estimated
        (parameter_values.transmission_rates
        / parameter_values.transmission_rate_unsuppressed).
        '''
        scale = (self.parameter_values.transmission_rates
                 / self.parameter_values.transmission_rate_unsuppressed)
        self.parameter_values.transmission_rate_unsuppressed *= scale
        self.parameter_values.transmission_rate_suppressed *= scale
        self.parameter_values.transmission_rate_acute *= scale

    def plot_estimates(self, ax, **kwargs):
        '''
        Make a horizontal line at the value of the geometric mean estimate.
        '''
        label = self.__class__.__name__
        ax.axhline(self.transmission_rates,
                   label = label,
                   **kwargs)


class Lognormal(Estimator):
    '''
    Estimate the transmission rate at each time,
    then build a lognormal random variable using statistics
    from the result.
    '''
    def estimate(self):
        '''
        Get the estimates of the transmission rate at each time
        and build a lognormal random variable.
        '''
        transmission_rates_vs_time = self.estimate_vs_time()

        gmean = stats.gmean(transmission_rates_vs_time)
        sigma = numpy.std(numpy.log(transmission_rates_vs_time), ddof = 1)

        # Note that the median of this lognormal RV is gmean.
        transmission_rates = stats.lognorm(sigma, scale = gmean)

        # scipy RVs don't define .mode (i.e. MLE),
        # so I explicitly add it so I can use it
        # as the point estimate later.
        transmission_rates.mode = gmean * numpy.exp(- sigma ** 2)

        return transmission_rates

    def set_transmission_rates(self):
        '''
        Scale parameters.transmission_rate_* by the estimated
        (parameter_values.transmission_rates
        / parameter_values.transmission_rate_unsuppressed).
        '''
        scale = (self.parameter_values.transmission_rates
                 / self.parameter_values.transmission_rate_unsuppressed)
        self.parameter_values.transmission_rate_unsuppressed *= scale
        self.parameter_values.transmission_rate_suppressed *= scale
        self.parameter_values.transmission_rate_acute *= scale

    def plot_estimates(self, ax,
                       quantile_levels = (0, 0.5, 0.9, 0.95),
                       **kwargs):
        '''
        Make horizontal lines at the median and other quantiles.
        '''
        label_base = self.__class__.__name__

        # Vary linestyle for the different quantile levels.
        # Hopefull 4 is enough...
        linestyles = pyplot.cycler(
            linestyle = ['solid', 'dashed', 'dashdot', 'dotted'])()
        # Remove linestyle from kwargs, if it's there.
        kwargs.pop('linestyle', None)
        for level in quantile_levels:
            if level == 0:
                quantiles = [0.5]
            else:
                quantiles = [0.5 - level / 2, 0.5 + level / 2]
            linestyle = next(linestyles)
            level_label_set = False
            for q in quantiles:
                if not level_label_set:
                    if q == 0.5:
                        label = '{} median'.format(label_base)
                    else:
                        label = '{} inner {:g}%tile'.format(label_base,
                                                            100 * level)
                    level_label_set = True
                else:
                    label = None
                ax.axhline(self.transmission_rates.ppf(q),
                           label = label,
                           **kwargs, **linestyle)


class LeastSquares(Estimator):
    r'''
    Estimate the transmission rates.

    The per-capita incidence is

    .. math:: i(t) = \lambda(t) \frac{S(t)}{N(t)}
              = \frac{\beta_U (U(t) + D(t)) + \beta_V V(t)}{N(t)}
              \frac{S(t)}{N(t)},

    assuming that acute transmission has only a small effect
    (:math:`\beta_A A(t) \ll \beta_U (U(t) + D(t))` and
    :math:`\beta_A A(t) \ll \beta_V V(t)`),
    that there are few treated people without viral suppression
    (:math:`T(t) \approx 0`), and that the AIDS class is small
    (:math:`W(t) \approx 0`).

    If :math:`p = \frac{U + D + V}{N}` is the prevalence and
    :math:`c = \frac{V}{U + D + V}` is the drug coverage,

    .. math:: i(t) = [\beta_U (1 - c(t)) + \beta_V c(t)] p(t) (1 - p(t)).

    Rearranging gives the least-squares problem

    .. math:: [(1 - c(t)) \beta_U + c(t) \beta_V]
              = \frac{i(t)}{p(t) (1 - p(t))},

    or

    .. math:: \mathbf{A} \mathbf{\beta} = \mathbf{b},

    with

    .. math:: \mathbf{A} =
              \begin{bmatrix}
              \vdots & \vdots \\
              1 - c(t) & c(t) \\
              \vdots & \vdots
              \end{bmatrix},

    .. math:: \mathbf{b} =
              \begin{bmatrix}
              \vdots \\
              \frac{i(t)}{p(t) (1 - p(t))} \\
              \vdots
              \end{bmatrix},

    and

    .. math:: \mathbf{\beta} =
              \begin{bmatrix}
              \beta_U \\ \beta_V
              \end{bmatrix}.
    '''
    def estimate(self):
        '''
        Use the least squares problem to estimate of the transmission
        rates.
        '''
        # Interpolate in case of any missing data.
        prevalence = self.parameters.prevalence.interpolate(method = 'index')
        incidence = self.parameters.incidence.interpolate(method = 'index')
        drug_coverage = self.parameters.drug_coverage.interpolate(
            method = 'index')

        # Set up A matrix and b vector.
        A = pandas.DataFrame([1 - drug_coverage, drug_coverage],
                             index = ('unsuppressed', 'suppressed')).T
        b = incidence / prevalence / (1 - prevalence)

        # Align them to the same years.
        A, b = A.align(b, axis = 0)

        # Drop years where there's missing data in either A or b.
        goodrows = A.notnull().all(axis = 1) & b.notnull()
        A = A[goodrows]
        b = b[goodrows]

        if len(A) > 0:
            betas, _, _, _ = numpy.linalg.lstsq(A, b)
        else:
            # No years with all data!
            betas = numpy.nan * numpy.ones(2)
        betas = pandas.Series(betas, index = A.columns)

        if any(betas < 0):
            warnings.warn(
                "country = '{}': ".format(self.country)
                + "Negative transmission rate '{}'.  ".format(betas[betas < 0])
                + 'Setting to 0.')
            betas[betas < 0] = 0

        if betas['suppressed'] > betas['unsuppressed']:
            warnings.warn(
                "country = '{}': ".format(self.country)
                + 'The transmission rate for people with viral suppression '
                + 'is higher than for people without viral suppression!')

        return betas

    def set_transmission_rates(self):
        '''
        Set unsuppressed and suppressed transmission_rates from estimates
        and leave acute as is.
        '''
        self.parameter_values.transmission_rate_unsuppressed \
            = self.transmission_rates['unsuppressed']
        self.parameter_values.transmission_rate_suppressed \
            = self.transmission_rates['suppressed']

    def plot_estimates(self, ax, **kwargs):
        '''
        Make horizontal lines at the values of the estimates.
        '''
        label_base = self.__class__.__name__
        # Vary linestyle for the different transmission rates.
        # Hopefull 4 is enough...
        linestyles = pyplot.cycler(
            linestyle = ['solid', 'dashed', 'dotted', 'dashdot'])()
        # Remove linestyle from kwargs, if it's there.
        kwargs.pop('linestyle', None)
        for (k, v) in self.transmission_rates.items():
            linestyle = next(linestyles)
            ax.axhline(v,
                       label = '{} {}'.format(label_base, k),
                       **kwargs, **linestyle)
    

def plot_all_estimators(country, Estimators = None, fig = None):
    '''
    Plot all estimator methods in the same figure.

    `Estimators = None` uses all defined estimators.
    '''
    if Estimators is None:
        Estimators = Estimator.__subclasses__()
    if fig is None:
        fig = pyplot.gcf()
    # Plot the data only on the first time through.
    plot_data = True
    for E in Estimators:
        e = E(country)
        e.plot(fig = fig, plot_data = plot_data)
        plot_data = False
        print('\t{}: R_0 = {:.2f}'.format(E.__name__, e.R0))
    return fig


def plot_all_countries(Estimators = None):
    '''
    Make a PDF with a page of all estimator plots for each country
    with data in the IncidencePrevalence datasheet.

    `Estimators = None` uses all defined estimators.
    '''
    countries = model.get_country_list('IncidencePrevalence')
    filename = '{}_all.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for country in countries:
            print(country)
            fig = pyplot.figure()
            plot_all_estimators(country, Estimators = Estimators, fig = fig)
            pdf.savefig(fig)
            pyplot.close(fig)


if __name__ == '__main__':
    country = 'South Africa'
    # print(country)
    # e = GeometricMean(country)
    # e = Lognormal(country)
    # e = LeastSquares(country)
    # print('transmission rate = {}'.format(e.transmission_rates))
    # e.plot()
    plot_all_estimators(country)
    pyplot.show()

    # plot_all_countries()
