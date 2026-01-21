from multiprocessing.connection import Connection
from typing import Any, Sequence

import matplotlib.pyplot as plt

from liveplot import request
from liveplot.logger import LOGGER
from liveplot.plotmanager import BasicPlotManager, BlitPlotManager, PlotManager

PLOT_LOGGER = LOGGER.getChild("plot")

DEFAULT_FIGSIZE = (6.0, 6.0)


class LivePlotBase:
    """
    Base class for live plots.
    """

    # Matplotlib objects.
    fig: plt.Figure
    """
    Figure this live plot is on.
    """
    ax: plt.Axes
    """
    Axes for this plot.
    """
    manager: PlotManager
    """
    ``PlotManager`` managing the plot.
    """

    # Basic plot info.
    title: str
    """
    Title of the plot.
    """
    xlabel: str
    """
    Label for the x-axis.
    """
    ylabel: str
    """
    Label for the y-axis.
    """
    figsize: tuple[float, float]
    """
    Figure size.
    """
    xlim: tuple[float, float] | None
    """
    Limits for the x-axis.
    """
    ylim: tuple[float, float] | None
    """
    Limits for the y-axis.
    """
    grid: bool
    """
    Whether to show grid lines.
    """
    initialized: bool
    """
    Toggled to ``True`` when the plot is initialized.
    """

    # Initialization methods.

    def __init__(
        self,
        title: str,
        xlabel: str = "x-label",
        ylabel: str = "y-label",
        figsize: tuple[float, float] = DEFAULT_FIGSIZE,
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        grid: bool = True,
        initialize_plot: bool = True,
    ):
        # Initialize all the instances variables.
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.figsize = figsize
        self.xlim = xlim
        self.ylim = ylim
        self.grid = grid
        self.initialized = False
        PLOT_LOGGER.debug(f"Created LivePlot object with title {self.title}.")

        if initialize_plot:
            # Initialize the plot and manager.
            self.init_plot()

    def init_plot(self):
        """
        Initializes the plot.
        """
        # Check if already initialized.
        if self.initialized:
            PLOT_LOGGER.error("Attempted to initialize plot more than once.")
            raise RuntimeError("Plot is already initialized.")
        # Initialize the figure.
        PLOT_LOGGER.debug("Initializing LivePlot.")
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
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
            # Use blitting manager for fixed axis limits.
            self.manager = BlitPlotManager(self.fig, self.ax)
        else:
            # If either limit is not defined, use the basic manager.
            self.manager = BasicPlotManager(self.fig, self.ax)
        # Layout the figure.
        self.fig.tight_layout()
        # Show the plot.
        plt.show(block=False)
        # Mark as initialized.
        self.initialized = True
        # Log the initialization as complete.
        PLOT_LOGGER.debug("LivePlot initialized.")

    # Updating method.

    def update(self):
        """
        Update the plot using the ``manager``.
        """
        # Recalculate limits if using basic manager.
        if isinstance(self.manager, BasicPlotManager):
            self.manager.relim()
            # Set any limits specified.
            if self.xlim:
                self.ax.set_xlim(self.xlim)
            if self.ylim:
                self.ax.set_ylim(self.ylim)
        # Redraw/update the plot.
        self.manager.update()


class LivePlotTrace(LivePlotBase):
    """
    A live plot with a single trace.
    """

    # Trace data.
    line: plt.Line2D
    """
    Line2D artist for the trace.
    """
    trace_kwargs: dict[str, Any]
    """
    Keyword arguments for the trace artist.
    """
    xdata: list[float]
    """
    X data for the trace.
    """
    ydata: list[float]
    """
    Y data for the trace.
    """

    def __init__(
        self,
        title: str,
        xlabel: str = "x-label",
        ylabel: str = "y-label",
        figsize: tuple[float, float] = DEFAULT_FIGSIZE,
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        grid: bool = True,
        initialize_plot: bool = True,
        trace_kwargs: dict[str, Any] | None = None,
    ):
        # Initialize the base class.
        super().__init__(
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            figsize=figsize,
            xlim=xlim,
            ylim=ylim,
            grid=grid,
            initialize_plot=initialize_plot,
        )

        # Initialize the trace data.
        self.xdata = []
        self.ydata = []
        # Set trace keyword arguments.
        self.trace_kwargs = trace_kwargs if trace_kwargs else {}

        # Initialize the line artists.
        (self.line,) = self.ax.plot(
            self.xdata,
            self.ydata,
            **self.trace_kwargs,
        )
        self.manager.add_artist(self.line)

    # Request handling methods.

    def add_point_handler(self, req: request.AddPoint) -> None:
        """Add a new point to the plot.

        Args:
            req (request.AddPoint): The add point request.
        """
        # Add the data from the request.
        self.xdata.append(req.x)
        self.ydata.append(req.y)
        self.line.set_data(self.xdata, self.ydata)
        # Update the plot.
        self.update()

    def add_point(self, x: float, y: float) -> None:
        """Add a new point to the plot.

        Args:
            x (float): The x value.
            y (float): The y value.
        """
        self.add_point_handler(request.AddPoint(x, y))

    def set_data_handler(self, req: request.SetData) -> None:
        """Set the trace data.

        Args:
            req (request.SetData): The set data request.
        """
        # Set the data from the request.
        self.xdata = list(req.xdata)
        self.ydata = list(req.ydata)
        self.line.set_data(self.xdata, self.ydata)
        # Update the plot.
        self.update()

    def set_data(self, xdata: Sequence[float], ydata: Sequence[float]) -> None:
        """Set the trace data.

        Args:
            xdata (Sequence[float]): The x data.
            ydata (Sequence[float]): The y data.
        """
        self.set_data_handler(request.SetData(xdata, ydata))

    def close_handler(self, _: request.Close) -> None:
        """Close the plot.

        Args:
            req (request.Close): The close request.
        """
        PLOT_LOGGER.debug("Closing LivePlot.")
        plt.close(self.fig)

    def close(self) -> None:
        """
        Close the plot.
        """
        self.close_handler(request.Close())

    # Main request handler.

    def handle_request(self, req: request.Request) -> bool:
        """Handle a request.

        Args:
            req (request.Request): The request to handle.
        """
        # Use the table to find the appropriate handler.
        handler_name = request.REQUEST_HANDLERS.get(type(req).__name__, None)
        # Check if a handler was found.
        if handler_name is None:
            # No handler found.
            PLOT_LOGGER.warning(
                f"No handler found for request of type {type(req).__name__}."
            )
            return False
        # Get the handler
        handler = getattr(self, handler_name, None)
        if handler is None:
            PLOT_LOGGER.warning(f"Handler method {handler_name} not found.")
            return False
        # Call the appropriate handler.
        handler(req)
        return True

    # Method for running within a separate process.

    def process(self, pipe: Connection) -> None:
        """Function to call within a seperate process to manage the plot
        through a PipeConnection.

        Args:
            pipe (PipeConnection): The pipe connection to receive requests through.
        """
        PLOT_LOGGER.debug("Starting plotting process loop.")
        # Check that the plot has not already been initialized.
        if self.initialized is True:
            PLOT_LOGGER.error("Plot process called with already initialized plot.")
        # Initialize the plot.
        self.init_plot()
        # Main loop to handle incoming requests.
        while True:
            command: Any = pipe.recv()
            if isinstance(command, request.Request):
                # Handle the request.
                self.handle_request(command)
            else:
                # Warn the user.
                PLOT_LOGGER.warning(
                    f"Plot process received unknown command type: {type(command).__name__}."
                )
