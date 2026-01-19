# liveplot

A lightweight and simple python package for live data plotting. This package allows for simple plotting of data as it comes in. It dynamically uses blitting to speed up redraws and optionally runs plotting in a seperate process so that the main script does not get slowed down.

## Basic Live Plotting

Live plotting is accomplished through the ``LivePlot`` object which puts together a simple plot. It takes arguments such as title, axis labels, axis limits, grid, and trace kwargs. See ``examples/ex1.py`` for an example. Note that if ``xlim`` or ``ylim`` is not set during initialization, this can drastically slow down the cost of plotting operations, especially for big datasets. Keep reading to find out why.

## Blitting

If both ``xlim`` and ``ylim`` are defined upon initialization, the ``LivePlot`` class will choose to use blitting, which basically means instead of redrawing the entire figure, plot, axes, and re-calculating plot limits, it will only redraw the trace each time there is an update. See ``examples/ex2.py`` for an example of plotting with blitting.

This is not a subtle difference. Redrawing the entire plot and recalculating limits is a costly operation.

    > python examples\ex1.py # Without blitting.
    Expected runtime: 10.000 seconds
    Actual runtime: 46.121 seconds

    > python examples\ex2.py # With blitting.
    Expected runtime: 10.0 seconds
    Actual runtime: 11.792 seconds

## Plotting in a seperate process

If you are very concerned about not slowing down your main thread for (for example) time-sensitive data acquisition, this is the solution for you. You can create a ``LivePlot``, initializing it with the ``initialize_plot=False`` argument and then pass it to a ``LivePlotProcess`` which will initialize the ``LivePlot`` in a seperate process. This can make sure your script does not slow down while you are plotting. Consider ``examples/ex3.py`` and ``examples/ex4.py``. In ``ex3.py`` we are doing the same thing as ``ex2.py`` but we've added a ``print`` statement that slows down our loop on each iteration, so it is not _quite_ as fast as before.

    > python examples/ex3.py
    Expected runtime: 10.000 seconds
    Actual runtime: 12.061 seconds

However, in ``ex4.py`` we have delegated the plotting to a seperate process, so our loop is not slowed down by redrawing the plots at all and the whole script actually executes _faster_ than before!

    > python examples/ex4.py
    Expected runtime: 10.000 seconds
    Actual runtime: 10.716 seconds
