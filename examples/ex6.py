import time

import numpy as np

from liveplot import LivePlotImage, LivePlotImageProcess

np.random.seed(0)


def make_data(shape: tuple[int, int], pct_full: float):
    # Make the base data.
    data = np.random.randn(*shape)
    grad_y = np.linspace(0, 10, shape[0]).reshape(-1, 1)
    data += grad_y
    grad_x = np.linspace(0, 10, shape[1]).reshape(1, -1)
    data += grad_x
    # Blank out some spots in the data.
    n_data = np.prod(shape)
    n_full = min(max(int(n_data * pct_full), 0), n_data)
    flat_data = data.flatten()
    flat_data[n_full:] = np.nan
    return flat_data.reshape(shape)


if __name__ == "__main__":
    plot = LivePlotImage(
        title="heatmap example",
        xlen=10,
        ylen=10,
        xlabel="my x-axis",
        ylabel="my y-axis",
        cmap="inferno",
        xlim=(10, 100),
        ylim=(0, 9),
        initialize_plot=False,
    )

    proc = LivePlotImageProcess(plot)

    for pct in np.linspace(0.1, 0.9, 100):
        proc.set_data(make_data((10, 10), pct))
        time.sleep(0.01)
