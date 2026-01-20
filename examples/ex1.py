import time

import numpy as np

from liveplot import TraceLivePlot

# Initialize the plot.
plot = TraceLivePlot(
    "Example 1",
    xlabel="Time",
    ylabel="Voltage",
    figsize=(5, 5),
    xlim=(0, 10),  # Not setting either xlim or ylim disables blitting.
    grid=True,
    trace_kwargs={"color": "xkcd:red", "marker": "o", "fillstyle": "none"},
)

# Data to plot.
x_data = np.linspace(0, 10, 1000)
y_data = np.sin(2 * np.pi * x_data)

# Delay per loop iteration.
delay = 0.01

# Record start time.
t_start = time.time()

# Plotting loop.
for x, y in zip(x_data, y_data, strict=True):
    plot.add_point(x, y)
    time.sleep(delay)

# Print expected and actual runtime.
print(f"Expected runtime: {delay * len(x_data):.3f} seconds")  # noqa: T201
print(f"Actual runtime: {time.time() - t_start:.3f} seconds")  # noqa: T201

# Close the plot.
plot.close()
