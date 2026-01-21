import multiprocessing as mp
import sys
from multiprocessing.connection import Connection
from typing import Sequence

from liveplot import request
from liveplot.logger import LOGGER
from liveplot.plot import LivePlotTrace

PROCESS_LOGGER = LOGGER.getChild("process")


class TraceLivePlotProcess:
    """Class for managing a ``TraceLivePlot`` instance within a seperate
    process.

    Args:
        plot: The ``TraceLivePlot`` instance to manage. Note that this instance must be initialized with the argument ``initialize_plot=False``.
    """

    plot: LivePlotTrace
    pipe: Connection
    _process: mp.Process

    def __init__(self, plot: LivePlotTrace):
        # Save the plot instance.
        self.plot = plot
        self.pipe, plotter_pipe = mp.Pipe()
        self._process = mp.Process(
            target=self.plot.process, args=(plotter_pipe,), daemon=True
        )
        try:
            self._process.start()
        except RuntimeError as e:
            PROCESS_LOGGER.error("Failed to start plotting process.")
            if (
                str(e)
                .strip()
                .startswith("An attempt has been made to start a new process")
            ):
                PROCESS_LOGGER.error(
                    "To use LivePlotProcess, the code that creates the process must be within a 'if __name__ == \"__main__\"' block."
                )
            for p in mp.active_children():
                p.terminate()
            PROCESS_LOGGER.error(
                "You may need to keyboard interrupt (Ctrl+C) to stop any hanging processes."
            )
            sys.exit(1)

    def send_request(self, req: request.Request):
        """Send a generic request to the plot.

        Args:
            req: The request to send.
        """
        self.pipe.send(req)

    def add_point(self, x: float, y: float):
        """Add a point to the plot.

        Args:
            x (float): The x value of the point.
            y (float): The y value of the point.
        """
        self.send_request(request.AddPoint(x, y))

    def set_data(self, xdata: Sequence[float], ydata: Sequence[float]):
        """Set the trace data.

        Args:
            xdata (Sequence[float]): The x data.
            ydata (Sequence[float]): The y data.
        """
        self.send_request(request.SetData(xdata, ydata))

    def close(self):
        """
        Close the plot and terminate the process.
        """
        # Send the close request.
        PROCESS_LOGGER.debug("Attempting to close plotting process.")
        self.send_request(request.Close())
        self._process.join(2)
        # Check if the process is still alive.
        if self._process.is_alive():
            PROCESS_LOGGER.debug("Forcefully terminating plotting process.")
            self._process.terminate()
        # Make absolutely sure that the process is closed.
        self._process.join()
        PROCESS_LOGGER.debug("Plotting process closed.")
