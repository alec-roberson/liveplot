"""``liveplot`` package.

This package provides user-friedly objects for creating live-updating plots in Python via ``matplotlib.pyplot``.

<href>https://github.com/alec-roberson/liveplot</href>
"""

from importlib.metadata import PackageNotFoundError, version

from .logger import debug_mode, info_mode
from .plot import LivePlot, LivePlotImage, LivePlotTrace
from .process import LivePlotImageProcess, LivePlotProcess, LivePlotTraceProcess

# Expose all imported classes and functions.

__all__ = [
    "LivePlot",
    "LivePlotImage",
    "LivePlotImageProcess",
    "LivePlotProcess",
    "LivePlotTrace",
    "LivePlotTraceProcess",
    "debug_mode",
    "info_mode",
]

# Set version.
try:
    __version__ = version("liveplot")
except PackageNotFoundError:
    __version__ = "0.0.0"
