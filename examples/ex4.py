import time

import numpy as np

from liveplot import LivePlotTrace, LivePlotTraceProcess

if __name__ == "__main__":
    # Initialize the plot.
    plot = LivePlotTrace(
        "Example 1",
        xlabel="Time",
        ylabel="Voltage",
        figsize=(5, 5),
        xlim=(0, 10),
        ylim=(1.2, -1.2),
        grid=True,
        trace_kwargs={"color": "xkcd:red", "marker": "o", "fillstyle": "none"},
        initialize_plot=False,  # You MUST set this to False when using TraceLivePlot in a seperate process.
    )

    # Create the plot process. This process will automaticall start upon initialization.
    proc = LivePlotTraceProcess(plot)

    # Data to plot.
    x_data = np.linspace(0, 10, 1000)
    y_data = np.sin(2 * np.pi * x_data)

    # Delay per loop iteration.
    delay = 0.01

    # Record start time.
    t_start = time.time()

    # Plotting loop.
    for x, y in zip(x_data, y_data, strict=True):
        print(f"Adding point: ({x:.3f}, {y:.3f})")  # noqa: T201
        proc.add_point(x, y)
        time.sleep(0.01)

    # Print expected and actual runtime.
    print(f"Expected runtime: {delay * len(x_data):.3f} seconds")  # noqa: T201
    print(f"Actual runtime: {time.time() - t_start:.3f} seconds")  # noqa: T201

    # Close the plot.
    proc.close()
