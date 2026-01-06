# Session 9: Training Pipeline (Without MLflow)

## Overview

This session focuses on building a complete training pipeline in Kedro without MLflow integration. We'll create nodes for data splitting, hyperparameter tuning, model training, and model saving. MLflow integration will be added in a later session.

## Part 1: Training Pipeline Structure

### Step 1: Create Training Pipeline Structure

Create the training pipeline directory and files:

1. In `src/ml_app_wind_draft/pipelines/`, create `training/` folder
2. Create `training/pipeline.py` file
3. Create `training/nodes.py` file
4. Create `training/utils.py` file (for helper functions)

### Step 2: Initialize Training Pipeline

In `pipelines/training/pipeline.py`, create the basic pipeline structure:

```python
from kedro.pipeline import Pipeline, node
from .nodes import train_test_split, tune_hyperparameters, fit_best_model

def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline([
        # Nodes will be added here
    ])
```

### Step 3: Add Training Pipeline Configuration

Add training pipeline parameters to `conf/base/parameters.yml`:

```yaml
training_pipeline:
  test_size: 0.2
  random_seed: 42
  n_trials: 10
  optuna_params:
    catboost:
      learning_rate: [0.01, 0.3]
      depth: [4, 10]
      l2_leaf_reg: [0.1, 10.0]
```

## Part 2: Creating Training Nodes

### Step 4: Create train_test_split() Node

Create a node that splits features and target into training and test sets:

**In `training/nodes.py`:**
```python
from sklearn.model_selection import train_test_split as sk_train_test_split
import pandas as pd

def train_test_split(
    features: pd.DataFrame,
    target: pd.Series,
    test_size: float,
    random_seed: int
) -> dict:
    """Split features and target into train and test sets."""
    x_train, x_test, y_train, y_test = sk_train_test_split(
        features,
        target,
        test_size=test_size,
        random_state=random_seed
    )
    
    return {
        "x_train": x_train,
        "x_test": x_test,
        "y_train": y_train,
        "y_test": y_test
    }
```

**Add to pipeline:**
```python
node(
    func=train_test_split,
    inputs=["features", "target", "params:training_pipeline.test_size", "params:training_pipeline.random_seed"],
    outputs=["x_train", "x_test", "y_train", "y_test"],
    name="train_test_split"
)
```

### Step 5: Create Generic Parameter Sampling Function

Create a function to sample hyperparameters from configuration:

**In `training/utils.py`:**
```python
import optuna
from typing import Dict, Any

def sample_optuna_params(trial: optuna.Trial, param_grid: Dict[str, Any]) -> Dict[str, Any]:
    """Sample hyperparameters from configuration grid."""
    params = {}
    for param_name, param_range in param_grid.items():
        if isinstance(param_range, list) and len(param_range) == 2:
            if isinstance(param_range[0], float):
                params[param_name] = trial.suggest_float(
                    param_name, param_range[0], param_range[1], log=True
                )
            else:
                params[param_name] = trial.suggest_int(
                    param_name, param_range[0], param_range[1]
                )
    return params
```

### Step 6: Create objective() Function

Create the Optuna objective function for hyperparameter tuning:

**In `training/utils.py`:**
```python
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import pandas as pd

def objective(
    trial: optuna.Trial,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    param_grid: Dict[str, Any],
    n_splits: int = 3,
    random_seed: int = 42
) -> float:
    """Optuna objective function for hyperparameter tuning."""
    # Sample hyperparameters
    params = sample_optuna_params(trial, param_grid)
    
    # Add fixed parameters
    params.update({
        "iterations": 100,  # Fixed for faster tuning
        "random_seed": random_seed,
        "loss_function": "RMSE",
        "verbose": False
    })
    
    # Cross-validation
    tscv = TimeSeriesSplit(n_splits=n_splits)
    cv_scores = []
    
    for train_idx, val_idx in tscv.split(x_train):
        x_train_cv = x_train.iloc[train_idx]
        x_val_cv = x_train.iloc[val_idx]
        y_train_cv = y_train.iloc[train_idx]
        y_val_cv = y_train.iloc[val_idx]
        
        # Scale features
        scaler = StandardScaler()
        x_train_scaled = scaler.fit_transform(x_train_cv)
        x_val_scaled = scaler.transform(x_val_cv)
        
        # Train model
        model = CatBoostRegressor(**params)
        model.fit(x_train_scaled, y_train_cv.values.ravel())
        
        # Predict and evaluate
        y_pred = model.predict(x_val_scaled)
        mape = np.mean(np.abs((y_val_cv.values - y_pred) / np.clip(np.abs(y_val_cv.values), 1e-8, None))) * 100
        cv_scores.append(mape)
    
    return np.mean(cv_scores)
```

### Step 7: Create tune_hyperparameters() Node

Create the hyperparameter tuning node:

**In `training/nodes.py`:**
```python
import optuna
from .utils import objective

def tune_hyperparameters(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    optuna_params: dict,
    n_trials: int,
    random_seed: int
) -> dict:
    """Tune hyperparameters using Optuna."""
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=random_seed)
    )
    
    study.optimize(
        lambda trial: objective(
            trial,
            x_train,
            y_train,
            optuna_params["catboost"],
            random_seed=random_seed
        ),
        n_trials=n_trials
    )
    
    return {
        "best_params": study.best_params,
        "best_score": study.best_value
    }
```

**Add to pipeline:**
```python
node(
    func=tune_hyperparameters,
    inputs=[
        "x_train",
        "y_train",
        "params:training_pipeline.optuna_params",
        "params:training_pipeline.n_trials",
        "params:training_pipeline.random_seed"
    ],
    outputs="best_hyperparameters",
    name="tune_hyperparameters"
)
```

### Step 8: Create fit_best_model() Node

Create a node to train the final model with best hyperparameters:

**In `training/nodes.py`:**
```python
from sklearn.preprocessing import StandardScaler
from catboost import CatBoostRegressor

def fit_best_model(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    best_params: dict,
    random_seed: int
) -> dict:
    """Train the final model with best hyperparameters."""
    # Prepare parameters
    params = best_params.copy()
    params.update({
        "iterations": 500,  # More iterations for final model
        "random_seed": random_seed,
        "loss_function": "RMSE",
        "verbose": False
    })
    
    # Scale features
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    
    # Train model
    model = CatBoostRegressor(**params)
    model.fit(x_train_scaled, y_train.values.ravel())
    
    return {
        "model": model,
        "scaler": scaler
    }
```

**Add to pipeline:**
```python
node(
    func=fit_best_model,
    inputs=[
        "x_train",
        "y_train",
        "best_hyperparameters",
        "params:training_pipeline.random_seed"
    ],
    outputs=["best_model", "x_scaler"],
    name="fit_best_model"
)
```

### Step 9: Configure Model Datasets

Add model and scaler datasets to `conf/base/catalog.yml`:

```yaml
best_model:
  type: joblib.JoblibDataset
  filepath: data/02_models/best_model.pkl

x_scaler:
  type: joblib.JoblibDataset
  filepath: data/02_models/x_scaler.pkl
```

Update the pipeline to save models:

```python
node(
    func=lambda model, scaler: {"model": model, "scaler": scaler},
    inputs=["best_model", "x_scaler"],
    outputs=["best_model", "x_scaler"],
    name="save_model"
)
```

### Step 10: Register Training Pipeline

Add the training pipeline to `src/ml_app_wind_draft/pipeline_registry.py`:

```python
from ml_app_wind_draft.pipelines.training.pipeline import create_pipeline as create_training_pipeline

def register_pipelines() -> dict:
    return {
        "training": create_training_pipeline(),
        # ... other pipelines
    }
```

Run the training pipeline:
```bash
kedro run --pipeline=training
```

## Part 3: Debugging Kedro Pipelines

### Step 11: Debugging in PyCharm

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

### Step 12: Debugging in VS Code

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

2. Set breakpoints in your code
3. Press F5 to start debugging


### Step 14: Using kedro-viz for Pipeline Visualization

Visualize your pipeline to understand data flow:

```bash
kedro viz
```

This opens a web interface where you can:
- See the pipeline structure
- Inspect node inputs and outputs
- View data catalog
- Track pipeline execution
