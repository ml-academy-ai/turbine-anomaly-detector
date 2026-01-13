## Overview

This session focuses on building a complete training pipeline in Kedro without MLflow integration. 
We'll create nodes for data splitting, hyperparameter tuning, model training, and model saving. 
MLflow integration will be added in a later session.


### Create the training pipeline directory and files:

1. In `src/ml_app_wind_draft/pipelines/`, create `training/` folder


2. Create `training/__init__.py` file


3. Create `training/pipeline.py` file


4. Create `training/nodes.py` file


5. Create `training/utils.py` file (for helper functions)

### Initialize Training Pipeline

In `pipelines/training/pipeline.py`, create the basic pipeline structure:

```python
from kedro.pipeline import Pipeline, node

def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline([
        # Nodes will be added here
    ])
```

### Start building nodes

Essentially, we need to replicate the `eval_model()` function. We see that the input
to the function are the splits of X and y. So, let's make it as our first node.

Remember that as the output from the Feature Engineering pipeline, we have features and target.
Then, we make it as an input to this function.

We can do similarly as we did in the Notebook where we divided by index. Here, 
I propose that we divide by the test fraction.

```python
def train_test_split(
    features: pd.DataFrame,
    target: pd.Series,
    params: dict[str, Any],
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Explicit temporal train / val / test split using index boundaries.
    """
    test_idx = int(features.shape[0] * (1 - params["test_fraction"]))
    x_train, x_test = features.iloc[:test_idx].copy(), features.iloc[test_idx:].copy()
    y_train, y_test = target.iloc[:test_idx].copy(), target.iloc[test_idx:].copy()

    return x_train, y_train, x_test, y_test
```

Now, here's the config:
```python
training_pipeline:
    test_fraction: 0.2
    n_folds: 3
```

Now, we can add the node to the Pipeline:
```python
node(
   func=train_test_split,
   inputs=["features_data", "target_data", "params:training_pipeline"],
   outputs=["x_train", "y_train", "x_test", "y_test"],
),
```

### Add Training Pipeline to the Pipeline Registry

To run the pipeline, we need to add it to the Pipeline Registry and run `kedro run`:
```python
from kedro.pipeline import Pipeline
from turbine_anomaly_detector.pipelines.feature_eng.pipeline import create_pipeline as create_feature_eng_pipeline
from turbine_anomaly_detector.pipelines.training.pipeline import create_pipeline as create_training_pipeline

def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    feature_eng_pipeline = create_feature_eng_pipeline()
    training_pipeline = create_training_pipeline()

    return {
        "__default__": feature_eng_pipeline + training_pipeline
    }
```


### One very useful feature is to know how to debug


Since for now we run the pipelines from CLI, here's the way we can debug it.


I use Pycharm debugger.


You can use Pycharm for Free, just need to Download Community Edition.


Then setup the debugger and see what are x_train, x_test, etc.


### Hyperparameter Tuning Implementation

Now, as we see from the section from Notebook 4 -  `CatBoost Bayesian Hyperparameter Tuning 
with Child Runs`, we need to implement Hyperparameter tuning.

Let's first create an overall node function and then implement step-by-step.

Let's copy-paste the final result that is very close to the code from the Notebook:

```python
def tune_hyperparameters(
    x_train: pd.DataFrame, y_train: pd.Series, params: dict[str, Any]
) -> dict[str, Any]:
    """
    Train a model by optimizing hyperparameters using Optuna.
    Parameters
    ----------
    x_train : pd.DataFrame
        Training features.
    y_train : pd.Series
        Training target values.
    params : Dict[str, Any]
        Configuration dictionary containing:
        - 'optuna_search': dict with keys:
            - 'n_trials': int, number of optimization trials to run
            - 'model': str, model name (e.g., 'CatBoost', 'RF')
            - 'model_params': dict, model-specific parameter search spaces
        - 'n_folds': int, number of CV folds (default: 3)

    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - 'best_params': Dict[str, Any], best hyperparameters found during optimization
        - 'cv_results': Dict[str, Any], cross-validation results from best model:
            - 'cv_mae': float, average MAE over CV folds
            - 'cv_rmse': float, average RMSE over CV folds
            - 'cv_mape': float, average MAPE over CV folds
    """
    seed = 42
    # 1) Create the study and optimize CV MAPE via objective()
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=seed),
    )
    study.optimize(
        lambda trial: objective(trial, x_train, y_train, params),
        n_trials=params["optuna_search"]["n_trials"],
    )

    # 2) Get best parameters
    best_params = study.best_params

    # 3) Re-evaluate best model to get full CV results
    model_name = params["optuna_search"]["model"]

    cv_results = eval_model(
        x_train=x_train,
        y_train=y_train,
        n_splits=params["n_folds"],
        model_name=model_name,
        model_params=best_params,
        seed=seed,
    )

    return {
        "best_params": best_params,
        "cv_metrics": {
            "cv_mae": cv_results["cv_mae"],
            "cv_rmse": cv_results["cv_rmse"],
            "cv_mape": cv_results["cv_mape"],
        },
    }
```

We see that first, we need to implement `objective`. Let's do that in `utils.py` because this is
neither a node nor a pipeline.

### Implementation of `objective`
Let's first copy the original function from the Notebook:

```python
def objective(
    trial: optuna.Trial, 
    x_train: np.ndarray, 
    y_train: np.ndarray, 
    x_test: np.ndarray, 
    y_test: np.ndarray
) -> float:
    """
    Optuna objective for CatBoost using eval_model and MLflow child runs.
    Minimizes cross-validated MAE (cv_mae).
    """
    np.random.seed(SEED)

    # ----- 1. Sample CatBoost hyperparameters -----
    params: Dict[str, Union[int, float, bool]] = {
        "iterations": 100,
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "depth": trial.suggest_int("depth", 4, 10),
        "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 0.1, 10.0, log=True),
        "random_seed": SEED,
        "loss_function": "RMSE",
        "verbose": False,
    }

    # ----- 2. Evaluate using your CV evaluator -----
    eval_results = eval_model(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        n_splits=3,
        model_name="CatBoost",
        model_params=params,
    )

    # ----- 3. Log as child MLflow run -----
    metrics = {
        "cv_mae": eval_results["cv_mae"],
        "cv_rmse": eval_results["cv_rmse"],
        "cv_mape": eval_results["cv_mape"],
        "test_mae": eval_results["test_mae"],
        "test_rmse": eval_results["test_rmse"],
        "test_mape": eval_results["test_mape"],
        "trial_number": trial.number,
    }
```

We see that here, we directly specify the parameter samples which is hardcoding.

Ideally what we want is, in the config we specify a model, the range of parameters and then 
run the optimizer.

Here's the example of how to specify the parameters in the config file.

```python
optuna_search:
    model: 'CatBoost'
    n_trials: 5
    model_params:
      CatBoost:
        iterations: 10
        random_seed: 42

        depth:
          range: [ 5, 12 ]
          log: False
          type: int

        learning_rate:
          range: [0.01, 0.3]
          log: True
          type: float

        l2_leaf_reg:
          range: [0.1, 10.0]
          log: True
          type: float

      RandomForest: # as an example
        n_estimators: 100
        max_depth:
          range: [20, 30]
          log: False
          type: int
```

To use this config and sample from the ranges, let's create this function:
```python
def sample_optuna_params(
    model_params: dict[str, Any], trial: optuna.Trial
) -> dict[str, Any]:
    """
    Samples Optuna hyperparameters from a trial.

    Parameters
    ----------
    model_params : Dict[str, Any]
        Dictionary mapping parameter names to their definitions. Can be:
        - Fixed values: int, float, str, bool (e.g., iterations: 50)
        - Search space: dict with "range", "log", "type" keys (e.g., depth: {range: [3, 10], log: False, type: int})
        - Categorical: list of values (e.g., loss_function: ["RMSE", "MAE"])
    trial : optuna.Trial
        The Optuna trial object used to suggest parameter values during optimization.

    Returns
    -------
    Dict[str, Any]
        Dictionary mapping parameter names to their sampled values from the trial.
    """

    param_grid = {}
    # Iterate through each parameter in the model configuration
    for param, values in model_params.items():
        # Check if parameter has a continuous range definition (with "range" and "log" keys)
        # This indicates a numeric parameter that should be sampled from a range
        if isinstance(values, dict) and "range" in values and "log" in values:
            # Check if the parameter type is integer (default is float)
            if values.get("type", "float") == "int":
                # Sample integer value from the specified range with optional log scaling
                param_grid[param] = trial.suggest_int(
                    param, values["range"][0], values["range"][1], log=values["log"]
                )
            else:
                # Sample float value from the specified range with optional log scaling
                param_grid[param] = trial.suggest_float(
                    param, values["range"][0], values["range"][1], log=values["log"]
                )
        elif isinstance(values, list):
            # Parameter is categorical - sample from a discrete list of possible values
            param_grid[param] = trial.suggest_categorical(param, values)
        else:
            # Parameter is a fixed value (int, float, str, bool, etc.) - pass through as-is
            param_grid[param] = values

    return param_grid

```
Now, we can put this to the `objective`.

```python
model = params["optuna_search"]["model"]
sampled_model_params = sample_optuna_params(
     params["optuna_search"]["model_params"][model], trial
 )
```

### Implementation of `eval_model`
Now, we have `sampled_parameters ` that we can pass to the `eval_model` which we will also modify.
```python
def eval_model(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    n_splits: int = 3,
    model_name: Literal["RF", "CatBoost"] = "RF",
    model_params: dict[str, Any] | None = None,
    seed: int = 42,
) -> dict[str, Any]:
    """
    Evaluate a time series model using TimeSeriesSplit cross-validation
    on the training set, then refit on the full train data and evaluate on test.

    Parameters
    ----------
    x_train : pd.DataFrame
        Training features.
    y_train : pd.Series
        Training target.
    n_splits : int, default=3
        Number of time-series CV folds.
    model_name : {'RF', CatBoost'}, default='RF'
        Model identifier.
    model_params : dict or None
        Keyword arguments for the selected model.
    seed : int, default=42
        Random seed for reproducibility.

    Returns
    -------
    results : dict
        - 'cv_mae'   : average MAE over CV folds
        - 'cv_rmse'  : average RMSE over CV folds
        - 'cv_mape'  : average MAPE over CV folds
        - 'model'      : fitted final model
        - 'x_scaler'   : fitted StandardScaler for X features
    """
    np.random.seed(seed)

    if model_params is None:
        model_params = {}

    tscv = TimeSeriesSplit(n_splits=n_splits)
    cv_mae_list = []
    cv_rmse_list = []
    cv_mape_list = []

    # Sliding Time Series Cross-Validation
    for _, (train_idx, val_idx) in enumerate(tscv.split(x_train), 1):
        x_train_cv = x_train.iloc[train_idx, :].copy()
        x_val_cv = x_train.iloc[val_idx, :].copy()
        y_train_cv = y_train.iloc[train_idx].copy()
        y_val_cv = y_train.iloc[val_idx].copy()

        # Scale features (to make it more general and applicable not only for tree-based models)
        x_scaler = StandardScaler()
        x_scaled_cv_train = x_scaler.fit_transform(x_train_cv)
        x_scaled_cv_val = x_scaler.transform(x_val_cv)

        y_train_cv_vals = y_train_cv.values.ravel()
        y_val_cv_vals = y_val_cv.values.ravel()

        # Construct model
        if model_name == "RF":
            model = RF(**model_params)
        elif model_name == "CatBoost":
            model = CatBoostRegressor(
                **model_params, allow_writing_files=False, verbose=False
            )

        else:
            raise ValueError(f"Unknown model_name: {model_name}")

        # Fit model and predict on validation set
        model.fit(x_scaled_cv_train, y_train_cv_vals)
        y_pred_cv = model.predict(x_scaled_cv_val)

        errors = compute_metrics(y_val_cv_vals, y_pred_cv)

        cv_mae_list.append(float(errors["mae"]))
        cv_rmse_list.append(float(errors["rmse"]))
        cv_mape_list.append(float(errors["mape"]))

    # Compute average metrics over all folds
    cv_mae = round(np.mean(cv_mae_list), 2)
    cv_rmse = round(np.mean(cv_rmse_list), 2)
    cv_mape = round(np.mean(cv_mape_list), 2)

    return {
        "cv_mae": cv_mae,
        "cv_rmse": cv_rmse,
        "cv_mape": cv_mape,
        "model": model,
        "x_scaler": x_scaler,
    }
```

Here, we need to implement `compute_metrics` function. 

This function will be used a lot of times
across many parts of our application: in Training pipeline, Inference pipeline and even in the User Interface.

So, when things are common and can be re-used, we can put them to some common directory.

So, let's create `src/turbine_anomaly_detector/common/metrics.py

```python
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


def compute_metrics(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
) -> dict[str, float]:
    """
    Compute MAE, RMSE, and MAPE metrics for regression predictions.

    Args:
        y_true: Ground truth values (Series or array)
        y_pred: Predicted values (Series or array)

    Returns:
        Dictionary with keys: 'mae', 'rmse', 'mape'
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = (
        np.mean(np.abs((y_true - y_pred) / np.clip(np.abs(y_true), 1e-8, None))) * 100
    )

    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
    }
```


### Then we change the eval_model part in the `objective`
```python
# Evaluate using CV evaluator (TimeSeriesSplit cross-validation)
eval_results = eval_model(
  x_train=x_train,
  y_train=y_train,
  model_name=model,
  model_params=sampled_model_params,
)
return eval_results["cv_mape"]
```


### Then we can add the node
```python
node(
    func=tune_hyperparameters,
    inputs=["x_train", "y_train", "params:training_pipeline"],
    outputs="tuning_results",
),
```

### Debugging in PyCharm

**Configure PyCharm Debugger for Kedro:**

1. Go to **Run** → **Edit Configurations**
2. Click **+** → **Python**
3. Configure:
   - **Name**: `Kedro Run`
   - **Module name**: `kedro`
   - **Parameters**: `run`
   - **Working directory**: `<project_root>` (your project directory)
   - **Python interpreter**: Select `.venv/bin/python`

4. Set breakpoints in your node functions (e.g., in `training/nodes.py`)
5. Click **Debug** (or press Shift+F9)

**Tips:**
- Set breakpoints directly in node functions
- Use "Evaluate Expression" to inspect variables
- Step through code to see data transformations

### Debugging in VS Code

**Configure VS Code Debugger:**

1. Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Kedro Run",
            "type": "python",
            "request": "launch",
            "module": "kedro",
            "args": ["run"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "justMyCode": false
        }
    ]
}
```