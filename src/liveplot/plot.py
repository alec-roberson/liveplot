from multiprocessing.connection import Connection
from typing import Any, Literal, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt

from liveplot.logger import LOGGER
from liveplot.plotmanager import BasicPlotManager, BlitPlotManager, PlotManager

PLOT_LOGGER = LOGGER.getChild("plot")

DEFAULT_FIGSIZE = (6.0, 6.0)


class LivePlotBase:
    """Base class for live plots."""

    # Matplotlib objects.
    fig: plt.Figure
    """Figure this live plot is on."""
    ax: plt.Axes
    """Axes for this plot."""
    manager: PlotManager
    """``PlotManager`` managing the plot."""

    # Basic plot info.
    title: str
    """Title of the plot."""
    xlabel: str
    """Label for the x-axis."""
    ylabel: str
    """Label for the y-axis."""
    figsize: tuple[float, float]
    """Figure size."""
    xlim: tuple[float, float] | None
    """Limits for the x-axis."""
    ylim: tuple[float, float] | None
    """Limits for the y-axis."""
    grid: bool
    """Whether to show grid lines."""
    initialized: bool
    """Toggled to ``True`` when the plot is initialized."""

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
        """Initializes the plot."""
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

    # Base update method.
    def update(self):
        """Update the plot using the ``manager``."""
        self.manager.update()

    # Methods for process handling.

    def _call_method(self, func: str, *args: Any) -> None:
        """Call a function on the plot instance.

        This is intended to be used when the plot is being managed through a pipe in a separate process.
        Args:
            func: The name of the function to call.
            *args: The arguments to pass to the function.
        """
        if not hasattr(self, func):
            PLOT_LOGGER.error(
                f"Attempted to call non-existent function '{func}' on LivePlot."
            )
            raise AttributeError(f"LivePlot has no function '{func}'.")
        else:
            method = getattr(self, func)
            if not callable(method):
                PLOT_LOGGER.error(
                    f"Attempted to call non-callable attribute '{func}' on LivePlot."
                )
                raise AttributeError(f"LivePlot attribute '{func}' is not callable.")
            method(*args)

    def process(self, pipe: Connection) -> None:
        """Function to call within a separate process to manage the plot
        through a PipeConnection.

        Args:
            pipe (PipeConnection): The pipe connection to receive requests through. This pipe should receive tuples like ``(function_name: str, *args)``.
        """
        PLOT_LOGGER.debug("Starting plotting process loop.")
        # Check that the plot has not already been initialized.
        if self.initialized is True:
            PLOT_LOGGER.error("Plot process called with already initialized plot.")
            raise RuntimeError("Plot process called with already initialized plot.")
        # Initialize the plot.
        self.init_plot()
        # Main loop to handle incoming requests.
        while True:
            if pipe.closed:
                PLOT_LOGGER.debug("Pipe closed, exiting plotting process loop.")
                break
            else:
                # Get the next function call.
                func_call: tuple[Any, ...] | None = pipe.recv()
                self._call_method(*func_call)


class LivePlotTrace(LivePlotBase):
    """A live plot with a single trace."""

    line: plt.Line2D
    """Line2D artist for the trace."""
    trace_kwargs: dict[str, Any]
    """Keyword arguments for the trace artist."""
    xdata: list[float]
    """X data for the trace."""
    ydata: list[float]
    """Y data for the trace."""

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
        # Initialize the trace data.
        self.xdata = []
        self.ydata = []

        # Set trace keyword arguments.
        self.trace_kwargs = trace_kwargs if trace_kwargs else {}

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

    def init_plot(self):
        """Initialize the plot."""
        # Run the base class init_plot.
        super().init_plot()
        # Initialize the line artists.
        (self.line,) = self.ax.plot(
            self.xdata,
            self.ydata,
            **self.trace_kwargs,
        )
        self.manager.add_artist(self.line)

    # Methods for updating the plot.

    def update(self):
        """Update the plot using the ``manager``."""
        # Recalculate limits if using basic manager.
        if isinstance(self.manager, BasicPlotManager):
            self.manager.relim()
            # Set any limits specified.
            if self.xlim:
                self.ax.set_xlim(self.xlim)
            if self.ylim:
                self.ax.set_ylim(self.ylim)
        # Redraw/update the plot.
        super().update()

    def add_point(self, x: float, y: float) -> None:
        """Add a new point to the plot.

        Args:
            x: The x value.
            y: The y value.
        """
        self.xdata.append(x)
        self.ydata.append(y)
        self.line.set_data(self.xdata, self.ydata)
        self.update()

    def set_data(self, xdata: Sequence[float], ydata: Sequence[float]) -> None:
        """Set the trace data.

        Args:
            xdata: The x data.
            ydata: The y data.
        """
        self.xdata = list(xdata)
        self.ydata = list(ydata)
        self.line.set_data(self.xdata, self.ydata)
        self.update()

    def close(self) -> None:
        """Close the plot."""
        PLOT_LOGGER.debug("Closing LivePlot.")
        plt.close(self.fig)


class LivePlotImage(LivePlotBase):
    """A LivePlot for 2D data.

    This class can only be used with data that is spaced on a regular grid.

    The plot includes a dynamic color bar that will update as the image data is updated. By default, the color bar limits will extend to the maximum and minimum values _ever_ encountered in the data, but this can be reset by calling ``set_data`` with ``relim_cbar=True``.
    """

    img: mpl.image.AxesImage
    """The image object on the plot."""
    xlen: int
    """The length of the x-axis data."""
    ylen: int
    """The length of the y-axis data."""
    cmap: str
    """The colormap to use for the image."""
    img_data: npt.NDArray[np.float64]
    """The data for the image."""
    vmin: float
    """Minimum value for the color scale."""
    vmax: float
    """Maximum value for the color scale."""
    origin: Literal["upper", "lower"]
    """Origin parameter for the image."""

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
        self.vmin = np.nan
        self.vmax = np.nan
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
        """Initialize the plot."""
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
        self.img.set_clim(vmin=-1.0, vmax=1.0)
        # Add the colorbar.
        self.cbar = self.fig.colorbar(self.img, ax=self.ax)
        # Tight layout again to account for colorbar.
        self.fig.tight_layout()

    def _relim_cbar(self, update_only: bool = True) -> None:
        """Recalculate the colorbar limits absolutely based on current data."""
        if update_only:
            # Get the current vmax/vmin.
            current_vmax = np.nanmax(self.img_data)
            current_vmin = np.nanmin(self.img_data)
            # Only update if limits have not been set or have been exceeded.
            if np.isnan(self.vmax) or self.vmax < current_vmax:
                self.vmax = current_vmax
            if np.isnan(self.vmin) or self.vmin > current_vmin:
                self.vmin = current_vmin

        else:
            # Recalculate completely.
            self.vmax = np.nanmax(self.img_data)
            self.vmin = np.nanmin(self.img_data)

        # Set the color limits for the image, ensuring they are not nan.
        self.img.set_clim(
            vmin=1.0 if np.isnan(self.vmax) else self.vmax,
            vmax=-1.0 if np.isnan(self.vmin) else self.vmin,
        )

    def update(self):
        """Update the plot."""
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
        super().update()

    def set_data(self, data: npt.NDArray[np.float64], relim_cbar: bool = False) -> None:
        """Set the image data for the plot.

        Args:
            data: The new image data.
            relim_cbar: Whether to recalculate the colorbar limits completely. If ``False``, the existing limits will only be changed if they are exceeded by the new data.
        """
        # Copy the data and update the image.
        self.img_data = np.copy(data)
        self.img.set_data(self.img_data)
        # Recalculate cbar limits.
        self._relim_cbar(update_only=not relim_cbar)
        # Update the plot.
        self.update()

    def add_point(self, y: int, x: int, z: float, relim_cbar: bool = False) -> None:
        """Add a point to the image data.

        Args:
            y: The y index of the point.
            x: The x index of the point.
            z: The value to set at the point.
            relim_cbar: Whether to recalculate the colorbar limits completely. If ``False``, the existing limits will only be changed if they are exceeded by the new data.
        """
        # Set the pixel value in the data.
        self.img_data[y, x] = z
        # Update the image data.
        self.img.set_data(self.img_data)
        # Recalculate cbar limits.
        self._relim_cbar(update_only=not relim_cbar)
