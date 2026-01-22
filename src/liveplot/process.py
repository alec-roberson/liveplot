"""Submodule for managing ``LivePlot`` objects via multiprocessing."""

import multiprocessing as mp
import sys
from multiprocessing.connection import Connection
from typing import Sequence

import numpy as np
import numpy.typing as npt

from .logger import LOGGER
from .plot import LivePlot

PROCESS_LOGGER = LOGGER.getChild("process")


class LivePlotProcess:
    """Class for managing an instance of ``LivePlot`` within a separate
    process. The seperate process is started upon initialization of this class.
    After intiialization, any method calls to this instance will be forwarded
    to the ``LivePlot`` via a pipe connection and the ``_call_method``
    function.

    Args:
        plot: The ``LivePlot`` instance to manage. Note that this instance must be initialized with the argument ``initialize_plot=False``.
    """

    plot: LivePlot
    pipe: Connection
    _process: mp.Process

    def __init__(self, plot: LivePlot):
        # Save the plot instance.
        self.plot = plot
        self.pipe, plotter_pipe = mp.Pipe()
        self._process = mp.Process(
            target=self.plot.process, args=(plotter_pipe,), daemon=True
        )
        try:
            self._process.start()
        except RuntimeError as e:
            # Check if this error had to do with __name__ == "__main__".
            PROCESS_LOGGER.error("Failed to start plotting process.")
            if (
                str(e)
                .strip()
                .startswith("An attempt has been made to start a new process")
            ):
                PROCESS_LOGGER.error(
                    "To use LivePlotProcess, the code that creates the process must be within a 'if __name__ == \"__main__\"' block."
                )
            # Kill all child processes.
            for p in mp.active_children():
                p.terminate()
            # Helpful message to user and exit.
            PROCESS_LOGGER.error(
                "You may need to keyboard interrupt (Ctrl+C) to stop any hanging processes."
            )
            sys.exit(1)

    def __getattr__(self, name: str) -> None:
        """Does nothing."""
        if name in self.__dict__:
            # If the attribute exists, return it.
            return self.__dict__[name]
        else:
            # Otherwise, pretend it is a method that sends a request to the plot.
            return lambda *args: self.pipe.send((name, *args))

    def close(self) -> None:
        """Close the plot and end the process."""
        PROCESS_LOGGER.debug("Closing LivePlotProcess.")
        # Send the close request and wait for the process to end.
        self.pipe.send(("close",))
        self._process.join(timeout=5)
        # Check if the process is still alive.
        if self._process.is_alive():
            PROCESS_LOGGER.warning(
                "Plotting process did not terminate in time. Forcing termination."
            )
            self._process.terminate()
        # Absolutely ensure the process is joined.
        self._process.join()


# The rest of these classes do nothing more than the base class, but they are helpful for type hinting.


class LivePlotTraceProcess(LivePlotProcess):
    """Class for managing an instance of ``LivePlotTrace`` within a separate
    process.

    Args:
        plot: The ``LivePlotTrace`` instance to manage. Note that this instance must be initialized with the argument ``initialize_plot=False``.
    """

    def add_point(self, x: float, y: float) -> None:
        """Add a new point to the plot.

        Args:
            x: The x value.
            y: The y value.
        """
        self.__getattr__("add_point")(x, y)

    def set_data(self, xdata: Sequence[float], ydata: Sequence[float]) -> None:
        """Set the trace data.

        Args:
            xdata: The x data.
            ydata: The y data.
        """
        self.__getattr__("set_data")(xdata, ydata)


class LivePlotImageProcess(LivePlotProcess):
    """Class for managing an instance of ``LivePlotImage`` within a separate
    process.

    Args:
        plot: The ``LivePlotImage`` instance to manage. Note that this instance must be initialized with the argument ``initialize_plot=False``.
    """

    def set_data(self, data: npt.NDArray[np.float64], relim_cbar: bool = False) -> None:
        """Set the image data for the plot.

        Args:
            data: The new image data.
            relim_cbar: Whether to recalculate the colorbar limits completely. If ``False``, the existing limits will only be changed if they are exceeded by the new data.
        """
        self.__getattr__("set_data")(data, relim_cbar)

    def add_point(self, y: int, x: int, z: float, relim_cbar: bool = False) -> None:
        """Add a point to the image data.

        Args:
            y: The y index of the point.
            x: The x index of the point.
            z: The value to set at the point.
            relim_cbar: Whether to recalculate the colorbar limits completely. If ``False``, the existing limits will only be changed if they are exceeded by the new data.
        """
        self.__getattr__("add_point")(y, x, z, relim_cbar)
