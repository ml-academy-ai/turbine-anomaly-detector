## Installing uv
For the Python environments and dependency resolutions, we will use uv.

Let's compare uv with other tools (slide).

Here's how to install uv.
https://docs.astral.sh/uv/getting-started/installation/

## Creating env with uv

## Setting Up a Virtual Environment with uv (Quick Reference)

Just an example, let's create a directory `mkdir project-example`:

```bash
mkdir project-example
```
- **Create the virtual environment with a specific Python version:**
```bash
cd project-example
uv venv .venv --python 3.12
uv init
```
**uv init** Creates a `pyproject.toml` file where we can see the project info and dependencies.

- **Activate the virtual environment:**
```bash
source .venv/bin/activate
```

Then add:
```bash
"numpy>=1.26,<2",
 ```

**Install dependencies (if you have a `pyproject.toml` file):**
```bash
uv sync
```

After running `uv sync`, it will create a uv.lock file. The uv.lock file captures the exact dependency 
versions resolved for the project and becomes the single source of truth for environments. 
Once committed, all installs (local, CI, production) use uv sync to recreate the same environment 
from the lock file, ensuring consistency and reproducibility.

To add a package, we can run:
```bash
uv add pandas
```

It will the add pandas to the `pyproject.toml` and to the lock file.


## Installing Kedro
But here, we started create the project and all the files from scratch.

In our course, we will use a Kedro ML Project template and Kedro ML Pipeline manager.

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
git commit -m "Initial commit"
```
2. On GitHub:
- Click New repository
- Name it - turbine-anomaly-detector
- Create repository

3. Run (copy from git)
```bash
git remote add origin https://github.com/ml-academy-ai/turbine-anomaly-detector.git
git branch -M main
git push -u origin main
```


# Data analysis
I prepared a complete data analysis with all the steps I want to show.

Some things we will still be covering and coding as we go when we need to look at someting further.

The main reason why we are NOT coding live in the Notebooks because:
- All of you are familar with coding in Jupyter and also a lot of code just create various plots.
- For the DS part of the course, I want to focus more on the methods and thinking like a Lead Data Scienttists and discussions about the analysis details.
- We will go to the important parts of the code in detail, so again we better spend time discussing things important
for the deep DS analysis.
- Ones we are done with notebooks, when we start building the applications, we will be coding live. Otherwise, we would need more sessions which would not provide any significant value for you.
- Anyway, the Notebooks will be full of comments so that you will be able to revisit this any time and fully understand it.