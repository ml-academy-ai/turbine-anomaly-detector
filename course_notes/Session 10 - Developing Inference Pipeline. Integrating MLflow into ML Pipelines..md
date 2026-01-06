## Part 1: Developing Inference Pipeline

### Step 1: Create Inference Pipeline Structure

Create the inference pipeline directory and files:

1. In `src/ml_app_wind_draft/pipelines/`, create `inference/` folder (if not exists)
2. Create `inference/pipeline.py` file
3. Create `inference/nodes.py` file

### Step 2: Create predict() Node

Create a node that makes predictions using the trained model:

**In `inference/nodes.py`:**
```python
import pandas as pd
from typing import Any

def predict(x: pd.DataFrame, best_model: Any) -> pd.Series:
    """
    Make predictions using a trained model on new data.
    
    Parameters
    ----------
    x : pd.DataFrame
        Input features for prediction. Must have the same columns as the
        training data (excluding the target column).
    best_model : Any
        Trained model object that has a `predict` method.
    
    Returns
    -------
    pd.Series
        Predicted target values for the input features.
    """
    return pd.Series(best_model.predict(x))
```

**Add to pipeline in `inference/pipeline.py`:**
```python
from kedro.pipeline import Pipeline, node
from .nodes import predict

def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline([
        node(
            func=predict,
            inputs=["features_data", "best_model"],
            outputs="y_pred",
            name="predict"
        ),
    ])
```

### Step 3: Handle Data Loading for Inference

**Problem:** The feature engineering pipeline takes training data as input, but for inference we need to load different data.

**Solution:** Create separate data loading pipelines for training and inference.

**Option 1: Create separate loading pipelines**

1. Create `load_training_data()` pipeline that loads training data
2. Create `load_inference_data()` pipeline that loads inference data
3. Both can use the same feature engineering pipeline

**Option 2: Parameterize the feature engineering pipeline**

Make the feature engineering pipeline accept a parameter to specify which dataset to load.

**For simplicity, we'll use Option 1:**

**In `pipeline_registry.py`, create separate pipelines:**
```python
def register_pipelines() -> dict:
    feature_eng_pipeline = create_feature_eng_pipeline()
    training_pipeline = create_training_pipeline()
    inference_pipeline = create_inference_pipeline()
    
    return {
        "training": feature_eng_pipeline + training_pipeline,
        "inference": feature_eng_pipeline + inference_pipeline,
    }
```

### Step 4: Add Input Datasets to Catalog

Add inference input datasets to `conf/base/catalog.yml`:

```yaml
# Inference input data
inference_features:
  type: pandas.ParquetDataset
  filepath: data/01_raw/inference_data.parquet

inference_target:
  type: pandas.ParquetDataset
  filepath: data/01_raw/inference_target.parquet

# Or if loading from database
inference_data_from_db:
  type: pandas.ParquetDataset
  filepath: data/01_raw/inference_data.parquet
```

### Step 5: Create Common Metrics Utility

Create a shared metrics computation function that can be used by both training and inference pipelines.

**Create `src/common/` directory structure:**
- `src/common/__init__.py`
- `src/common/metrics.py`

**In `src/common/metrics.py`:**
```python
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import pandas as pd

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

### Step 6: Add compute_metrics() Node to Inference Pipeline

**In `inference/nodes.py`:**
```python
from common.metrics import compute_metrics as _compute_metrics
import numpy as np
import pandas as pd

def compute_metrics(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
) -> dict[str, float]:
    """
    Compute metrics for the predictions.
    
    Node function that wraps the common compute_metrics implementation.
    """
    return _compute_metrics(y_true, y_pred)
```

**Add to pipeline:**
```python
node(
    func=compute_metrics,
    inputs=["target_data", "y_pred"],
    outputs="metrics",
    name="compute_metrics"
)
```

**Print metrics in the node (optional):**
```python
def compute_metrics(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
) -> dict[str, float]:
    """Compute metrics and print them."""
    metrics = _compute_metrics(y_true, y_pred)
    print(f"MAE: {metrics['mae']:.2f}")
    print(f"RMSE: {metrics['rmse']:.2f}")
    print(f"MAPE: {metrics['mape']:.2f}%")
    return metrics
```

### Step 7: Register Inference Pipeline

Add the inference pipeline to `src/ml_app_wind_draft/pipeline_registry.py`:

```python
from ml_app_wind_draft.pipelines.inference.pipeline import create_pipeline as create_inference_pipeline

def register_pipelines() -> dict:
    return {
        "training": create_training_pipeline(),
        "inference": create_inference_pipeline(),
        # ... other pipelines
    }
```

Run the inference pipeline:
```bash
kedro run --pipeline=inference
```

### Step 8: Test Inference Pipeline

1. Make sure you have:
   - A trained model saved in `data/02_models/best_model.pkl`
   - Inference data in `data/01_raw/inference_data.parquet`
   - Target data (if available) in `data/01_raw/inference_target.parquet`

2. Run the pipeline:
   ```bash
   kedro run --pipeline=inference
   ```

3. Check the outputs:
   - Predictions should be generated
   - Metrics should be computed (if target data is available)

---

## Part 2: Integrating MLflow into Training Pipeline

### Step 6: Add MLflow Integration

**Problem:** We don't log any training parameters, metrics, etc to MLflow. Also, we save the model locally and not in the MLflow server (even local for now).

#### Adding MLflow Training Tracking + Model Registry

**Step 6.1: Create MLflow Hook**

Every time when we train the model, we need to point to the MLflow server. To set up such background processes, there's a mechanism in Kedro called **hooks**.

1. To add a hook, create `hooks.py` file
2. Add MLflow Hook that runs before any pipeline run
3. Add hook to `settings.py` file

**Emphasize:** It's convenient to run the code for specific pipelines and nodes.

After adding, run `kedro run`.

**Step 6.2: Create log_to_mlflow() Node**

Create `log_to_mlflow()` node.

**Step 6.3: Create MLModelWrapper**

When coming to `mlflow.pyfunc.log_model()`, say that we need to create `MLModelWrapper`, say that we need a general wrapper. Create this in `utils.py`.

**Step 6.4: Explain the log_to_mlflow() Function**

Explain the function step by step:

1. **Create a local directory for model artifacts** if it does not exist
2. **Start a new MLflow run** (all logs belong to this run)
3. **Log training metrics and best hyperparameters**
4. **Build an MLflow input–output signature** from a small input example
5. **Save the trained model and fitted scaler** as local artifact files
6. **Log a PyFunc model** that bundles model + scaler logic
7. **MLflow copies local artifact files** into its artifact store (local or remote)
8. **Local files can be deleted safely** after the run completes

Run `kedro training pipeline`, see the logged metrics and artifacts.

**Step 6.5: Create register_model() Node**

Create `register_model()` node.

**Tell about model registry stages and migration from them to aliases and tags:**
https://github.com/mlflow/mlflow/issues/10336

**Return version** to force promotion node run after the registry node.

**Step 6.6: Create validate_challenger() Node**

Create `validate_challenger()` node, explain its logic. Run the pipeline.

**Step 6.7: Update Inference Pipeline to Load Model from Registry**

Now that we're using MLflow to register models, update the inference pipeline to load models from the MLflow registry instead of local files.

**Update `inference/nodes.py`:**

Create a `load_from_registry()` function:

```python
from common.mlflow_utils import load_model_by_alias
from typing import Any

def load_from_registry(registered_model_name: str) -> Any:
    """
    Load the champion model from MLflow model registry by alias.
    
    Parameters
    ----------
    registered_model_name : str
        The name of the registered model in MLflow (e.g., 'wind_power_predictor').
    
    Returns
    -------
    Any
        The loaded champion model (MLflow pyfunc model) with scaler bundled.
        This model can be used directly for predictions as it handles scaling internally.
    """
    return load_model_by_alias(registered_model_name, alias="champion")
```

**Update the inference pipeline:**

```python
node(
    func=load_from_registry,
    inputs=["params:mlflow.registered_model_name"],
    outputs="best_model",
    name="load_from_registry"
),
node(
    func=predict,
    inputs=["features_data", "best_model"],
    outputs="y_pred",
    name="predict"
),
```

**Note:** The model loaded from MLflow registry already includes the scaler (bundled in the PyFunc model), so the `predict()` node doesn't need a separate `x_scaler` input. The model handles scaling internally.

**Note:** In kedro-mlflow plugin, there's such a dataset. However, mlflow develops quickly and it can be the case that at some point these dataset might not match. Also, it's easy to do and we get more control over it.