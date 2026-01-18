from typing import Any

import matplotlib.pyplot as plt

from liveplot.logger import LOGGER
from liveplot.plotmanager import BasicPlotManager, BlitPlotManager, PlotManager
from liveplot.request import AddPoint, Request

PLOT_LOGGER = LOGGER.getChild("plot")


class LivePlot:
    """
    A live plot of a single trace that can have its data updated.
    """

    # Matplotlib objects.
    fig: plt.Figure
    ax: plt.Axes
    line: plt.Line2D
    manager: PlotManager

    # Basic plot info.
    title: str
    xlabel: str
    ylabel: str
    figsize: tuple[float, float]
    xlim: tuple[float, float] | None
    ylim: tuple[float, float] | None
    trace_kwargs: dict[str, Any]
    grid: bool

    # Data for plotting.
    xdata: list[float]
    ydata: list[float]

    def __init__(
        self,
        title: str,
        xlabel: str = "X",
        ylabel: str = "Y",
        figsize: tuple[float, float] = (8.0, 6.0),
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        trace_kwargs: dict[str, Any] | None = None,
        grid: bool = True,
    ):
        # Initialize all the instances variables.
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.figsize = figsize
        self.xlim = xlim
        self.ylim = ylim
        self.trace_kwargs = trace_kwargs if trace_kwargs is not None else {}
        self.grid = grid
        self.xdata = []
        self.ydata = []
        PLOT_LOGGER.debug(f"Created LivePlot object with title {self.title}.")

        # Initialize the plot and manager.
        self._init_plot()

    def _init_plot(self):
        """
        Initialize the plot.
        """
        # Make the plot and add the line.
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
        (self.line,) = self.ax.plot(self.xdata, self.ydata, **self.trace_kwargs)
        # Set title and labels.
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        # Set grid and limits.
        if self.grid:
            self.ax.grid(self.grid)
        if self.xlim:
            self.ax.set_xlim(self.xlim)
        if self.ylim:
            self.ax.set_ylim(self.ylim)
        # Create the appropriate plot manager.
        if self.xlim is not None and self.ylim is not None:
            self.manager = BlitPlotManager(self.fig, self.ax)
            self.manager.add_artist(self.line)
        else:
            self.manager = BasicPlotManager(self.fig, self.ax)
        # Show the plot.
        plt.show(block=False)
        # Mark as initialized.
        PLOT_LOGGER.debug("Plot initialized.")

    def update(self):
        """
        Update the plot with new data.
        """
        # Update trace data.
        self.line.set_xdata(self.xdata)
        self.line.set_ydata(self.ydata)
        # Recalculate limits if using basic manager.
        if isinstance(self.manager, BasicPlotManager):
            self.manager.relim()
            # Set any limits specified.
            if self.xlim:
                self.ax.set_xlim(self.xlim)
            if self.ylim:
                self.ax.set_ylim(self.ylim)
        # Update the plot.
        self.manager.update()

    def add_point(self, req: AddPoint):
        """
        Add a new point to the plot.
        """
        # Add the data from the request.
        self.xdata.append(req.x)
        self.ydata.append(req.y)
        # Update the plot.
        self.update()

    def handle_request(self, req: Request):
        """
        Handle an incoming request.
        """
        if isinstance(req, AddPoint):
            self.add_point(req)
        else:
            raise ValueError(f"Unknown request type: {type(req).__name__}.")
