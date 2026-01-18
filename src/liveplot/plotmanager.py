from typing import Any

import matplotlib as mpl
from matplotlib.backends.backend_agg import FigureCanvasAgg

from liveplot.logger import LOGGER

MANAGER_LOGGER = LOGGER.getChild("manager")


class PlotManager:
    """
    Base class for plot managers.
    """

    fig: mpl.figure.Figure
    ax: mpl.axes.Axes
    _artists: list[mpl.artist.Artist]

    def __init__(
        self,
        fig: mpl.figure.Figure,
        ax: mpl.axes.Axes,
    ):
        # Initialize all the instances variables.
        self.fig = fig
        self.ax = ax
        self._artists = []

    def add_artist(self, artist: mpl.artist.Artist):
        """
        Add an artist to the plot.
        """
        # Check figure.
        if artist.figure != self.fig:
            raise RuntimeError("Artist figure does not match PlotManager figure.")
        # Add to the list of artists.
        self._artists.append(artist)
        self.ax.add_artist(artist)

    def update(self):
        """Update the plot.

        To be implemented by subclasses.
        """
        raise NotImplementedError("Update method must be implemented by subclasses.")


class BasicPlotManager(PlotManager):
    """
    A basic plot manager that redraws the entire plot every time there is an
    update.
    """

    def __init__(
        self,
        fig: mpl.figure.Figure,
        ax: mpl.axes.Axes,
    ):
        super().__init__(fig, ax)
        MANAGER_LOGGER.debug("Initialized BasicPlotManager.")

    def relim(self):
        """
        Recalculate limits based on current artists.
        """
        MANAGER_LOGGER.debug("Recalculating axis limits.")
        self.ax.relim()
        self.ax.autoscale_view()

    def update(self):
        """
        Redraw the canvas and flush events.
        """
        MANAGER_LOGGER.debug("Redrawing the plot.")
        # Redraw the canvas.
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        # Layout the figure again.
        self.fig.tight_layout()


class BlitPlotManager(PlotManager):
    """
    A plot manager that uses blitting to optimize redraws.
    """

    canvas: FigureCanvasAgg
    _bg: None | Any

    def __init__(
        self,
        fig: mpl.figure.Figure,
        ax: mpl.axes.Axes,
        animated_artists=(),
    ):
        super().__init__(fig, ax)
        self.canvas = fig.canvas
        self._bg = None

        # Add all the artists.
        for a in animated_artists:
            self.add_artist(a)

        # Grab the background on every draw.
        self.cid = self.canvas.mpl_connect("draw_event", self.on_draw)
        MANAGER_LOGGER.debug("Initialized BlitPlotManager.")

    def add_artist(self, artist: mpl.artist.Artist):
        """
        Add an artist and enable animation.
        """
        artist.set_animated(True)
        super().add_artist(artist)

    def on_draw(self, event):
        """Callback to register with "draw_event".

        Grabs th background and draws all the artists.
        """
        # Check the event canvas.
        if event is not None:
            if event.canvas != self.canvas:
                raise RuntimeError(
                    "Event canvas does not match BlitPlotManager canvas."
                )
        # Copy the background and draw animated artists.
        self._bg = self.canvas.copy_from_bbox(self.canvas.figure.bbox)
        self._draw_animated()

    def _draw_animated(self):
        """
        Draw all animated artists.
        """
        for a in self._artists:
            self.ax.draw_artist(a)

    def update(self):
        """
        Update the animated artists via blitting.
        """
        # Paranoia in case we missed the draw event.
        if self._bg is None:
            self.on_draw(None)
        else:
            # Restore the background
            self.canvas.restore_region(self._bg)
            # Draw all of the animated artists.
            self._draw_animated()
            # Update the GUI state.
            self.canvas.blit(self.canvas.figure.bbox)
        # Let the GUI event loop process anything it has to do.
        self.canvas.flush_events()
