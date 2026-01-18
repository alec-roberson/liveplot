import pathlib
import subprocess
import sys

path = pathlib.Path(__file__).parent

pip_args = [
    "install",
    "--no-dependencies",
    "--no-build-isolation",
    "--no-index",
    "-e",
    str(path),
]

if __name__ == "__main__":
    sys.exit(subprocess.call(["python", "-m", "pip", *pip_args]))
