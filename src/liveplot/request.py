from collections.abc import Sequence


class Request:
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
    """
    Request to add a point to the plot.
    """

    x: float
    y: float

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class SetData(Request):
    """
    Request to set the trace data.
    """

    xdata: list[float]
    ydata: list[float]

    def __init__(self, xdata: Sequence[float], ydata: Sequence[float]):
        self.xdata = list(xdata)
        self.ydata = list(ydata)
