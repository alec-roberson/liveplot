class Request:
    """
    Base class for all requests.
    """

    pass


class AddPoint(Request):
    """
    Request to add a point to the plot.
    """

    x: float
    y: float
    trace: str | None

    def __init__(self, x: float, y: float, trace: str | None = None):
        self.x = x
        self.y = y
        self.trace = trace
