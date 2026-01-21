from multiprocessing.connection import Connection
from typing import Any, Literal, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt

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
        plt.pause(0.05)
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


class LivePlot2DWithColorBar(LivePlotBase):
    """A live plot for 2D data.

    This plot includes a dynamic color bar that will update as the image
    data is updated.

    This class assumes that the data is linearly spaced within the
    specified x and y bounds.
    """

    img: mpl.image.AxesImage
    """
    The image object on the plot.
    """
    xlen: int
    """
    The length of the x-axis data.
    """
    ylen: int
    """
    The length of the y-axis data.
    """
    cmap: str
    """
    The colormap to use for the image.
    """
    img_data: npt.NDArray[np.float64]
    """
    The data for the image.
    """
    vmin: float | None
    """
    Minimum value for the color scale.
    """
    vmax: float | None
    """
    Maximum value for the color scale.
    """
    origin: Literal["upper", "lower"]
    """
    Origin parameter for the image.
    """

    def __init__(
        self,
        title: str,
        xlen: int,
        ylen: int,
        xlabel: str = "x-label",
        ylabel: str = "y-label",
        cmap: str = "inferno",
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        figsize: tuple[float, float] = DEFAULT_FIGSIZE,
        origin: Literal["upper", "lower"] = "lower",
        initialize_plot: bool = True,
    ):
        # Save the instance variables.
        self.xlen = xlen
        self.ylen = ylen
        self.cmap = cmap
        self.vmin = None
        self.vmax = None
        self.origin = origin

        # Require limits on the axes.
        xlim = xlim if xlim else (0, xlen)
        ylim = ylim if ylim else (0, ylen)

        # Expand the limits to line up axes ticks.
        x_step = np.abs(xlim[1] - xlim[0]) / xlen
        y_step = np.abs(ylim[1] - ylim[0]) / ylen
        xlim = (xlim[0] - x_step / 2, xlim[1] + x_step / 2)
        ylim = (ylim[0] - y_step / 2, ylim[1] + y_step / 2)

        # Initialize the base class.
        super().__init__(
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            figsize=figsize,
            xlim=xlim,
            ylim=ylim,
            grid=False,  # No grid for image plots.
            initialize_plot=initialize_plot,
        )

    def init_plot(self):
        """
        Initialize the plot.
        """
        # Run the base class init_plot.
        super().init_plot()
        # Delete the assigned plot manager and replace it with a BasicPlotManager.
        del self.manager
        self.manager = BasicPlotManager(self.fig, self.ax)
        # Initialize image data.
        self.img_data = np.zeros((self.ylen, self.xlen))
        self.img_data[:] = np.nan
        # Initialize the image.
        self.img = self.ax.imshow(
            self.img_data,
            cmap=self.cmap,
            extent=(*self.xlim, *self.ylim),
            origin=self.origin,
            aspect="auto",
        )
        # Set initial color limits (no data yet).
        self.img.set_clim(vmin=-1, vmax=1)
        # Add the colorbar.
        self.cbar = self.fig.colorbar(self.img, ax=self.ax)
        # Tight layout again to account for colorbar.
        self.fig.tight_layout()

    def update(self):
        """
        Update the plot.
        """
        # Update color limits based on data.
        current_vmax = np.nanmax(self.img_data)
        current_vmin = np.nanmin(self.img_data)

        if self.vmax is None or self.vmax < current_vmax:
            self.vmax = current_vmax
        if self.vmin is None or self.vmin > current_vmin:
            self.vmin = current_vmin

        self.img.set_clim(
            vmin=self.vmin,
            vmax=self.vmax,
        )

        # Redraw/update the plot.
        self.manager.update()

    def set_data(self, data: npt.NDArray[np.float64], relim_cbar: bool = False) -> None:
        """Set the image data for the plot.

        Args:
            data: The new image data.
            relim_cbar: Whether to recalculate the colorbar limits completely. If ``False``, the existing limits will only be changed if they are exceeded by the new data.
        """
        # Copy the data and update the image.
        self.img_data = np.copy(data)
        self.img.set_data(self.img_data)

        # Recalculate cbar limits if requested.
        if relim_cbar:
            self.vmax = np.nanmax(self.img_data)
            self.vmin = np.nanmin(self.img_data)

    def add_point(self, y: int, x: int, z: float) -> None:
        """Add a point to the image data.

        Args:
            y: The y index of the point.
            x: The x index of the point.
            z: The value to set at the point.
        """
        self.img_data[y, x] = z
