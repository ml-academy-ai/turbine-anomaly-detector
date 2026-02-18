## Intro
### Explain slides with `Why use Code Quality Checks` and `Code Quality Checks Types` list.
### Explain each `Code Quality Check`, from `Linting` to `Pytest`
### Explain cheatsheet slide with `ruff commands`

## Part 1: Linting with Ruff

### Step 1: Install Ruff

If not installed, run:
```bash
uv add ruff
```

### Step 2: Check pyproject.toml

Verify that ruff is added to your dependencies.

### Step 3: Run Ruff Check

Run:
```bash
ruff check .
```

**What to expect:**
- We got > 600 errors.
- It can find A LOT of errors even though we tried to keep our code clean, add typings, remove unused imports, etc.
- However, it covered everything including notebooks

### Step 4: Exclude Notebooks

**Why exclude notebooks?**
- In notebooks, code quality is less important because it does not go to production
- Notebooks are for exploration and experimentation

**To exclude notebooks:**

In `pyproject.toml`, add to the existing `[tool.ruff]` key:
```toml
[tool.ruff]
line-length = 88
show-fixes = true
extend-exclude = [
    "*.ipynb",  # Excludes all Jupyter Notebooks
    "notebooks/",
]

```

### Now, we have much fewer errors.

### Step 5: Check Individual Files or directories

Let's run it for one directory - `feature_eng_pipeline`
```bash
ruff check src/turbine_anomaly_detector/pipelines/feature_eng
```

Discuss some errors:
- Import sorting
- Unused imports
- Type hints
- Code style

### Step 6: Auto-fix Errors

Fix the errors. Run:
```bash
ruff check . --fix
```

This also fixes import sorting automatically.

### Step 7: Check Remaining Errors
```bash
ruff check .
```
Check when errors still exist. It might not fix errors that it **CANNOT fix without intervention**. Resolve or ignore these manually.

 - Add `# noqa: E402` for imports not at the top
 - For too many arguments, use `# noqa: PLR0913`
 - Use  `# noqa: PLR0913` for `conf.py` functions
 - Change `Magic Numbers` practice in test. Ask Cursor why it's bad
 - Add outlier values at `conftest.py`
```python
OUTLIER_HIGH = 200
OUTLIER_LOW = -10

@pytest.fixture
def dataset_with_outliers(HIGH_POWER, LOW_POWER):
    """Small synthetic dataset with outliers in one column only."""
    n = 15
    timestamps = pd.date_range("2024-01-01", periods=n, freq="h")
    # Smooth series
    t = np.linspace(0, 2 * np.pi, n)
    power = 50 + 10 * np.sin(t)

    df = pd.DataFrame({"power": power, "Timestamps": timestamps})

    # Outliers in power only
    df.loc[5, "power"] = HIGH_POWER   # spike
    df.loc[10, "power"] = LOW_POWER  # impossible drop
    return df
```
- Use values in the tests
```python
from tests.conftest import OUTLIER_HIGH, OUTLIER_LOW

def test_remove_diff_outliers_one_column(dataset_with_outliers):
    result = remove_diff_outliers(
        dataset_with_outliers,
        diff_thresholds={"power": 30},
    )
    assert result.notna().values.all() # make sure no NaN values are introduced
    assert result["power"].iloc[5] != OUTLIER_HIGH  # make sure the outlier is removed
    assert result["power"].iloc[10] != OUTLIER_LOW # make sure the outlier is removed

```

---

## Part 2: Formatting with Ruff

### Step 1: Check What Would Be Formatted

First, run:
```bash
ruff format --check .
```

This shows what would be formatted (but not formatted yet).

### Step 2: Format Code

To format, run:
```bash
ruff format .
```

### Step 3: Verify

Then run:
```bash
ruff check .
```

(Should be all fixed)

---

### Introduce an error intentionally
- Go to `feature_eng pipeline nodes`
- Modify `def smooth_signal`
```python
df_smoothed[col] = (
                df_smoothed[col]
                .rolling(window=window, min_periods=1, center=False)
                .mean()
            )
```
to
```python
df_smoothed[col] = (df_smoothed[col].rolling(window=window, min_periods=1, center=False).mean())
```

### Run
```bash
ruff format . --check
```

### Run 
```bash
ruff format .
```
## Part 3: Type Checking with ty

### Step 1: Install ty

Run:
```bash
uv add ty
```

**Note:** `ty` is created by the ruff creators, so it integrates well with ruff.

### Step 2: Run Type Check

Run:
```bash
ty check .
```

### Step 3: Configure ty

Add to `pyproject.toml`:
```toml
[tool.ty.src]
include = ["src", "tests", "entrypoints"]
```

### Step 4: Handle MLflow Type Errors

For mlflow errors, add:
```toml
[[tool.ty.overrides]]
include = ["**/pipelines/**"]
rules = { "possibly-missing-attribute" = "ignore" }
```

This ignores MLflow's dynamic attribute access that type checkers can't understand.

### For pandas column problem, just add `# type: ignore`

### Introduce some typing errors, for instance, `src/turbine/monitoring/nodes`:
 - Change int ---> bool
```python
def get_retraining_trigger(
    wasserstein_distance: float,
    threshold: float,
) -> int:
    """
    Determine if retraining is needed based on Wasserstein distance.
    """
    if wasserstein_distance > threshold:
        return 1
    else:
        return 0
```
### Say typings are especially helpful for Pandas and numpy array catches, or Returns.
- Go to `src/turbine/pipelines/feature_eng/nodes`
```python
def remove_diff_outliers(
    df: pd.DataFrame, diff_thresholds: dict[str, float]
) -> pd.DataFrame:
    """
    Remove outliers based on absolute first-order diff and forward-fill the gaps.
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    diff_thresholds : dict[str, float]
        Dictionary of column names and their corresponding absolute diff thresholds.

    Returns
    -------
    df_clean : pd.DataFrame
        Cleaned dataframe with forward fill.
    """
    df_clean = df.copy()

    for col, threshold in diff_thresholds.items():
        # 1. Compute absolute diff
        diff_vals = df_clean[col].diff(1).abs()

        # 2. Outlier mask
        outlier_mask = diff_vals > threshold
        outlier_idx = df_clean.index[outlier_mask]

        # 3. Remove outliers
        df_clean.loc[outlier_idx, col] = np.nan

        # 4. Forward fill (and backfill if needed)
        df_clean[col] = df_clean[col].ffill().bfill()

    return df_clean
```
- Move `df_clean` under the `for-loop` and run inference pipeline. It runs in both cases.
- However, if we run `ty check .`
- Change back the `return` statement

### We can ignore the typing errors, if we want
```toml
[tool.ty.rules]
invalid-argument-type = "ignore"
invalid-return-type = "ignore"
not-subscriptable = "ignore"
unresolved-attribute = "ignore"
```
---

## Part 4: Pre-commit Framework

### Introduction

### Show `pre-commit git hook manager` slide
### Show `Pre-commit Git hook manager setup` steps and follow them

### Step 1: Install Pre-commit

Let's install pre-commit framework:
```bash
uv add pre-commit
```

### Step 2: Create Pre-commit Config

Create a file named `.pre-commit-config.yaml`

### Step 3: Configure Ruff for Pre-commit

#### Google "pre-commit ruff" and take the file from the git repo of ruff-pre-commit.

**What is nice:** The pre-commit-config is already compatible with `pyproject.toml`, 
so we can keep our setup and just add vanilla config for pre-commit.

We should get similar to:
```yaml
repos:
- repo: https://github.com/astral-sh/ruff-pre-commit
  # Ruff version.
  rev: v0.15.1
  hooks:
    # Run the linter.
    - id: ruff-check
      types_or: [ python, pyi ]
      args: [ --fix ]
    # Run the formatter.
    - id: ruff-format
      types_or: [ python, pyi ]
```

#### Google "pre-commit ty" and take the file from the git repo of ruff-pre-commit.
Instead of the repo version, we will use this:
```yaml
- repo: local
  hooks:
    - id: ty-check
      name: ty check
      entry: uv run ty check src tests
      language: system
      types_or: [python, pyi]
      exclude: ^notebooks/
      pass_filenames: false
```

We run this versio because:
- We already installed ty in your project with uv
- We want to run it via your exact project environment

### Step 4 Install Git Hook
A Git hook is a script that Git executes automatically before or after specific actions like commit, push, or merge.
Run:
```bash
pre-commit install
```

This installs the Git hook.

### Step 5: Verify Hook Installation

Run:
```bash
ls -l .git/hooks/pre-commit
```

To see if the hook is installed. It's added to the hidden `.git` file (at least for Mac), so we will not see it in the Editor.


### Step 6: Test Pre-commit

Now, we can run:
```bash
pre-commit run --all-files
```

### Step 7: Demonstrate Auto-fix on Commit

Now, if we change some imports sorting and then commit changes, it will:
- Automatically fix the issues it can fix:
```bash
ruff check . --fix`
```
- Leave the issues it cannot fix (for manual resolution)

### Step 9: Add ty to Pre-commit

Google "how to add ty to pre-commit". Add the config.

Now pre-commit will:
- Run ruff (linting and formatting)
- Run ty (type checking)
- All automatically before each commit

---