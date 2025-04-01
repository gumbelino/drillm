import os
import subprocess
import sys


def install_pip():
    """Ensure pip is installed."""
    try:
        import pip
    except ImportError:
        print("Installing pip...")
        subprocess.check_call([sys.executable, "-m", "ensurepip"])
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]
        )


def install_pyenv():
    """Install pyenv if it doesn't exist."""
    try:
        subprocess.check_output(["pyenv", "--version"], stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing pyenv...")
        subprocess.check_call(["brew", "install", "pyenv"])
        # Add pyenv to PATH in the current session
        os.environ["PATH"] += os.pathsep + os.path.expanduser("~/.pyenv/bin")
        subprocess.check_call(["eval", "$(pyenv init --path)"], shell=True)


def setup_pyenv():
    """Set up Python versions and virtual environments according to Pipfile."""
    if not os.path.exists("Pipfile"):
        print("No Pipfile found. Skipping pyenv setup.")
        return

    # Install dependencies from Pipfile
    subprocess.check_call(["pip", "install", "pipenv"])
    subprocess.check_call(["pipenv", "install"])


def setup_renv():
    """Set up R environment according to renv.lock."""
    if not os.path.exists("renv.lock"):
        print("No renv.lock found. Skipping renv setup.")
        return

    # Install renv and dependencies
    subprocess.check_call(["brew", "install", "r"])
    subprocess.check_call(
        [
            "Rscript",
            "-e",
            "if (!requireNamespace('renv', quietly = TRUE)) install.packages('renv')",
        ]
    )

    # Restore the R environment from renv.lock
    subprocess.check_call(["Rscript", "-e", "renv::restore()"])


def main():
    install_pip()
    install_pyenv()
    setup_pyenv()
    setup_renv()


if __name__ == "__main__":
    main()
