## Installing uv
https://docs.astral.sh/uv/getting-started/installation/

## Installing Kedro
For our porject, we will use a Kedro ML Project template.

Kedro is ML pipeline manager which also forces an ML project to follow a certain structure. We can start using structure after creating a project with Kedro.

To do that, we run:

```bash
uvx --python 3.12 kedro new
```

**Project name:** `ml-wind-turbine-anomaly` (use only lower letters)

**Select option 1-5** (because we will not use pyspark)

**No example pipeline** - select "No" when asked

**Open project in IDE**


## Configure Python Version

Change in `pyproject.toml`:
```toml
requires-python = ">=3.12<3.13"
```

Then run
```bash
uv venv .venv
```

Then activate
```bash
source .venv/bin/activate
```

Check that Python is using the virtual environment:
```bash
which python

```
Run:
```bash
uv sync
```

## Installing Dependecies

1. To install a single package, we can do: 
```bash
uv add numpy
```
Then, if we look at the pyproject.toml file, we will see this package in the list.

1. Instead, we can add this directly to the toml

```bash
  "numpy>=1.26,<2",
  "pandas>=2.2,<3",
  "pyarrow>=14,<21",
  "python-dateutil>=2.8,<3",
  "pyyaml>=6,<7",

  "scikit-learn>=1.4,<1.5",
  "catboost>=1.2,<1.3",
  "optuna>=4,<5",
  "shap<0.50",

  "torch>=2.2,<2.3",
  "torchvision>=0.17,<0.18",
  "torchaudio>=2.2,<2.3",

  "mlflow>=3.6,<3.7",

  "ipython>=8.10,<9",
  "notebook>=7,<8",
  "jupyterlab>=4.0,<5",
  "ipywidgets>=8,<9",

  "ydata-profiling>=4.16,<5",
  "matplotlib>=3.8,<4",
  "seaborn>=0.13,<0.14",
```

To install these packages, we run:

```bash
uv pip install -e .
```

Then, in the uv.lock file, we will get the exact package versions. We also can list them using:

```bash
uv pip list
```

If we want to install the fixed dependecies, we run:
```bash
uv sync
```

## Configure Interpreter

In your IDE (PyCharm/VSCode), configure the Python interpreter to use `.venv/bin/python`.

##  Copy Data and create EDA Notebook

Copy your data files **df_train_test.parquet** and **df_prod.parquet** to `data/01_raw/` directory.

Create your first EDA notebook (e.g., `notebooks/01 - EDA.ipynb`).

## Overview of the Package After Creation

### Understanding egg-info

In `src/`, you can find `egg-info` directory.

**What is egg-info?**
- `egg-info` is a directory created by setuptools during package installation.
- **Setuptools** is a Python library that helps you package, build, and distribute your Python code. It's the tool that makes it possible to install Python packages using `pip`.
- It contains metadata about your Python package
- You can safely delete it

# Creating a Git Repo

1. Run
```bash
git init
```
```bash
git status
git add .
git commit -m "Initial Kedro project setuInitial commit
```
