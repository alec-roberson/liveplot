from collections.abc import Sequence
from typing import NamedTuple

REQUEST_HANDLERS = {
    "AddPoint": "add_point",
    "SetData": "set_data",
    "Close": "close",
}
"""
Dictionary mapping of request class names to ``LivePlot`` handler method names.
"""


class Request(NamedTuple):
    """
    Base class for all requests.
    """

    pass


class Close(Request):
    """
    Request to close the plot.
    """

    pass


class AddPoint(Request):
    """Request to add a point to the plot.

    Args:
        x (float): The x value.
        y (float): The y value.
    """

    x: float
    y: float


class SetData(Request):
    """Request to set the trace data.

    Args:
        xdata (Sequence[float]): The x data.
        ydata (Sequence[float]): The y data.
    """

    xdata: Sequence[float]
    ydata: Sequence[float]
