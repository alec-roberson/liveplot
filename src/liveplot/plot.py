from multiprocessing.connection import PipeConnection
from typing import Any, Sequence, overload

import matplotlib.pyplot as plt

from liveplot import request
from liveplot.logger import LOGGER
from liveplot.plotmanager import BasicPlotManager, BlitPlotManager, PlotManager

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
    initialized: bool

    # Data for plotting.
    xdata: list[float]
    ydata: list[float]

    # Initialization methods.

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
        initialize_plot: bool = True,
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
        self.initialized = False
        PLOT_LOGGER.debug(f"Created LivePlot object with title {self.title}.")

        if initialize_plot:
            # Initialize the plot and manager.
            self.init_plot()

    def init_plot(self):
        """
        Initialize the plot.
        """
        # Check if already initialized.
        if self.initialized:
            PLOT_LOGGER.error("Attempted to initialize plot more than once.")
            raise RuntimeError("Plot is already initialized.")
        PLOT_LOGGER.debug("Initializing LivePlot.")
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
        # Layout the figure.
        self.fig.tight_layout()
        # Mark as initialized.
        self.initialized = True
        PLOT_LOGGER.debug("LivePlot initialized.")

    # Updating method.

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

    # Request handling methods.
    @overload
    def add_point(self, req: request.AddPoint) -> None:
        """Add a new point to the plot.

        Args:
            req (request.AddPoint): The add point request.
        """
        ...

    @overload
    def add_point(self, x: float, y: float) -> None:
        """Add a new point to the plot.

        Args:
            x (float): The x value.
            y (float): The y value.
        """
        ...

    def add_point(
        self, req_or_x: request.AddPoint | float, y: float | None = None
    ) -> None:
        # Check which overload was used.
        if y is not None:
            req = request.AddPoint(req_or_x, y)
        else:
            req = req_or_x
        # Add the data from the request.
        self.xdata.append(req.x)
        self.ydata.append(req.y)
        # Update the plot.
        self.update()

    @overload
    def set_data(self, req: request.SetData) -> None:
        """Set the trace data.

        Args:
            req (request.SetData): The set data request.
        """
        ...

    @overload
    def set_data(self, xdata: Sequence[float], ydata: Sequence[float]) -> None:
        """Set the trace data.

        Args:
            xdata (Sequence[float]): The x data.
            ydata (Sequence[float]): The y data.
        """
        ...

    def set_data(
        self,
        req_or_xdata: request.SetData | Sequence[float],
        ydata: Sequence[float] | None = None,
    ) -> None:
        # Check which overload was used.
        if ydata is not None:
            req = request.SetData(req_or_xdata, ydata)
        else:
            req = req_or_xdata
        # Set the data from the request.
        self.xdata = list(req.xdata)
        self.ydata = list(req.ydata)
        # Update the plot.
        self.update()

    @overload
    def close(self, req: request.Close) -> None:
        """Close the plot.

        Args:
            req (request.Close): The close request.
        """
        ...

    @overload
    def close(self) -> None:
        """
        Close the plot.
        """
        ...

    def close(self, _: request.Close | None = None) -> None:
        # Doesn't matter which overload was used.
        PLOT_LOGGER.debug("Closing LivePlot.")
        plt.close(self.fig)

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

    def process(self, pipe: PipeConnection) -> None:
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
