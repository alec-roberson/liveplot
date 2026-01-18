import multiprocessing as mp
import sys
from multiprocessing.connection import PipeConnection

from liveplot import request
from liveplot.logger import LOGGER
from liveplot.plot import LivePlot

PROCESS_LOGGER = LOGGER.getChild("process")


class LivePlotProcess:
    """Class for managing a ``LivePlot`` instance within a seperate process.

    Args:
        plot: The ``LivePlot`` instance to manage. Note that this instance must be initialized with the argument ``initialize_plot=False``.
    """

    plot: LivePlot
    pipe: PipeConnection
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

    def add_point(self, x: float, y: float):
        """Add a point to the plot.

        Args:
            x: The x value of the point.
            y: The y value of the point.
        """
        self.pipe.send(request.AddPoint(x, y))

    def close(self):
        """
        Close the plot.
        """
        self.pipe.send(request.Close())

    def send_request(self, req: request.Request):
        """Send a generic request to the plot.

        Args:
            req: The request to send.
        """
        self.pipe.send(req)
