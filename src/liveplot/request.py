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
