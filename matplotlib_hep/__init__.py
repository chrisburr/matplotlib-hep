from __future__ import division

import numpy as np
import scipy.stats as stats


__all__ = ['histpoints', 'make_split', 'calc_nbins', 'plot_pull']


def calc_nbins(x, maximum=150):
    n = (max(x) - min(x))
    n /= (2 * len(x)**(-1/3) * (np.percentile(x, 75) - np.percentile(x, 25)))
    return np.floor(min(n, maximum))


def poisson_limits(N, kind, confidence=0.6827):
    if kind == 'gamma':
        alpha = 1 - confidence
        lower = stats.gamma.ppf(alpha / 2, N)
        upper = stats.gamma.ppf(1 - alpha / 2, N + 1)
    elif kind == 'sqrt':
        err = np.sqrt(N)
        lower = N - err
        upper = N + err
    else:
        raise ValueError('Unknown errorbar kind: {}'.format(kind))
    # clip lower bars
    lower[N == 0] = 0
    assert len(lower) == len(upper) == len(N)
    return np.array(N - lower), np.array(upper - N)


def histpoints(x, bins=None, xerr=None, yerr='gamma', normed=False, scale=1,
               **kwargs):
    """
    Plot a histogram as a series of data points.

    Compute and draw the histogram of *x* using individual (x,y) points
    for the bin contents.

    By default, vertical poisson error bars are calculated using the
    gamma distribution.

    Horizontal error bars are omitted by default.
    These can be enabled using the *xerr* argument.
    Use ``xerr='binwidth'`` to draw horizontal error bars that indicate
    the width of each histogram bin.

    Parameters
    ---------

    x : (n,) array or sequence of (n,) arrays
        Input values. This takes either a single array or a sequence of
        arrays, which are not required to be of the same length.

    """
    import matplotlib.pyplot as plt

    if bins is None:
        bins = calc_nbins(x)

    h, bins = np.histogram(x, bins=bins)
    width = bins[1] - bins[0]
    center = (bins[:-1] + bins[1:]) / 2
    area = sum(h * width)

    if isinstance(yerr, str):
        yerr = poisson_limits(h, yerr)

    if xerr == 'binwidth':
        xerr = width / 2

    if normed:
        h = h / area
        yerr = yerr / area
        area = 1.

    h = h * scale
    yerr = yerr[0] * scale, yerr[1] * scale
    area = area * scale

    if 'color' not in kwargs:
        kwargs['color'] = 'black'

    if 'fmt' not in kwargs:
        kwargs['fmt'] = 'o'

    plt.errorbar(center, h, xerr=xerr, yerr=yerr, **kwargs)

    return center, (yerr[0], h, yerr[1]), area


def make_split(ratio, gap=0.12):
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    cax = plt.gca()
    box = cax.get_position()
    xmin, ymin = box.xmin, box.ymin
    xmax, ymax = box.xmax, box.ymax
    gs = GridSpec(2, 1, height_ratios=[ratio, 1 - ratio],
                  left=xmin, right=xmax, bottom=ymin, top=ymax)
    gs.update(hspace=gap)

    ax = plt.subplot(gs[0])
    plt.setp(ax.get_xticklabels(), visible=False)
    bx = plt.subplot(gs[1], sharex=ax)

    return ax, bx


def plot_pull(data, func):
    import numpy as np
    import matplotlib.pyplot as plt

    ax, bx = make_split(0.8)

    plt.sca(ax)

    x, y, norm = histpoints(data)

    lower, upper = ax.get_xlim()

    xs = np.linspace(lower, upper, 200)
    plt.plot(xs, norm * func(xs), 'b-')

    plt.sca(bx)

    resid = y[1] - norm * func(x)
    err = np.zeros_like(resid)
    err[resid >= 0] = y[0][resid >= 0]
    err[resid < 0] = y[2][resid < 0]

    pull = resid / err

    plt.errorbar(x, pull, yerr=1, color='k', fmt='o')
    plt.ylim(-5, 5)
    plt.axhline(0, color='b')

    plt.sca(ax)

    return ax, bx
