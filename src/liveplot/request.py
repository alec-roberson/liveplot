from collections.abc import Sequence
from typing import NamedTuple, TypeAlias

REQUEST_HANDLERS = {
    "AddPoint": "add_point_handler",
    "SetData": "set_data_handler",
    "Close": "close_handler",
}
"""
Dictionary mapping of request class names to ``LivePlot`` handler method names.
"""


class AddPoint(NamedTuple):
    """Request to add a point to the plot.

    Args:
        x (float): The x value.
        y (float): The y value.
    """

    x: float
    y: float


class SetData(NamedTuple):
    """Request to set the trace data.

    Args:
        xdata (Sequence[float]): The x data.
        ydata (Sequence[float]): The y data.
    """

    xdata: Sequence[float]
    ydata: Sequence[float]


class Close(NamedTuple):
    """
    Request to close the plot.
    """

    pass


Request: TypeAlias = AddPoint | SetData | Close
