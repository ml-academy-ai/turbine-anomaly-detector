# Adding MLflow Training Tracking + Model Registry

As you remember, if we want to add things to MLflow, we need to have 2 things:
1. Up and running MLflow Server.
2. We need to set tracking URI.

We make the MLflow Server Up only once and it's supposed to be always running.

However, now, when we run our ML Pipelines every time, we need to setup a tracking URI,
both the Training, Inference and later Monitoring Pipeline.

We CAN potentially write it as nodes, but ideally we want the nodes to make opeartions
on either data or ML models.

For such background processes, in Kedro there's a concept called Hooks (show slides.)


### Create MLflow Hook

Every time when we train the model, we need to point to the MLflow server. To set up such background processes.

1. To add a hook, create `src/turbine_anomaly_detector/hooks.py` file
2. Inside `hook.py`, add:
```python
class MLFlowHook:
    """Project hooks for MLflow tracking URI setup."""

    @hook_impl
    def before_pipeline_run(self, run_params, pipeline, catalog):
        """Set MLflow tracking URI before pipeline runs.

        Uses environment variable if set, otherwise falls back to localhost:5001
        for local development. In Docker, the environment variable should be set
        to http://mlflow:5001 (internal service name).
        """
        print(f"Setting MLflow tracking URI")
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:8080")
        mlflow.set_tracking_uri(tracking_uri)
```
3. Add hook to `settings.py` file:
```python
from turbine_anomaly_detector.hooks import MLFlowHook

HOOKS = (MLFlowHook(),)
```
4. After adding, start the server: 
```python
mlflow server \
  --host 127.0.0.1 \
  --port 8080 \
  --backend-store-uri sqlite:///mlflow/mlflow.db \
  --default-artifact-root mlflow/artifacts
```

5. Run `kedro run`. It runs and we can see the printed statement.

### Logging models and runs to MLflow.

1. Create `log_to_mlflow()` node and go through the code.

```python
def log_to_mlflow(
    hyperparams_tuning_results: dict[str, Any],
    train_results: dict[str, Any],
    train_pipeline_params: dict[str, Any],
    mlflow_params: dict[str, Any],
) -> str:
    """
    Log model, metrics, and parameters to MLflow.

    Parameters
    ----------
    hyperparams_tuning_results : dict[str, Any]
        Contains 'best_params' and 'cv_metrics' (cv_mae, cv_rmse, cv_mape).
    train_results : dict[str, Any]
        Contains 'model', 'x_scaler', 'input_example', and 'test_metrics'.
    train_pipeline_params : dict[str, Any]
        Contains 'optuna_search' with 'model' key.
    mlflow_params : dict[str, Any]
        Contains 'prod_experiment_name'.

    Returns
    -------
    str
        Model URI of the logged PyFunc model.
    """
    # Set MLflow tracking URI and experiment
    mlflow.set_experiment(mlflow_params["prod_experiment_name"])

    # Get model name and determine run name
    model_name = train_pipeline_params["optuna_search"]["model"]
    # Default run name with timestamp for uniqueness
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_name = f"{model_name}_{timestamp}_candidate"

    # Create temporary directory for artifacts
    temp_models_dir = Path("data/06_models")
    temp_models_dir.mkdir(parents=True, exist_ok=True)

    with mlflow.start_run(run_name=run_name):
        # Log metrics and parameters
        mlflow.log_metrics(hyperparams_tuning_results["cv_metrics"])
        mlflow.log_metrics(train_results["test_metrics"])
        mlflow.log_params(hyperparams_tuning_results["best_params"])

        # Create signature from input example
        input_example = train_results["input_example"]
        x_scaler = train_results["x_scaler"]
        best_model = train_results["model"]
        y_example = best_model.predict(x_scaler.transform(input_example))
        signature = infer_signature(input_example, y_example)

        # Save model and scaler artifacts depending on the model type
        if model_name.lower() == "catboost":
            model_path = temp_models_dir / "catboost_model.cbm"
            best_model.save_model(str(model_path))
        elif model_name.lower() in ["rf", "random_forest"]:
            model_path = temp_models_dir / "random_forest_model.pkl"
            joblib.dump(best_model, model_path)
        else:
            raise ValueError(f"Unknown model_name: {model_name}")

        scaler_path = temp_models_dir / "x_scaler.joblib"
        joblib.dump(x_scaler, scaler_path)

        # Prepare artifacts dictionary for MLModelWrapper
        artifacts = {
            "model": str(model_path),
            "scaler": str(scaler_path),
        }

        # Log PyFunc model using MLModelWrapper
        model_info = mlflow.pyfunc.log_model(
            name="model",
            python_model=MLModelWrapper(model_name=model_name),
            artifacts=artifacts,
            signature=signature,
            input_example=input_example,
            tags={
                "best_model": "true",
                "model_type": model_name,
                "run_name": run_name,
            },
        )
    # 8) Return model URI to later register the model
    return model_info.model_uri
```

2. Add parameters to the config
```python
mlflow:
  prod_experiment_name: prod_model_training
  registered_model_name: wind_power_predictor
```

### Adding MLModelWrapper and compare with the one from Notebook

Let's add MLModelWrapper to `.utils.py`
```python
class MLModelWrapper(mlflow.pyfunc.PythonModel):
    """
    PyFunc model wrapper with bundled scaler.
    Expects unscaled, feature-engineered DataFrame.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name.lower()

    def load_context(self, context):
        # load scaler
        self.scaler = joblib.load(context.artifacts["scaler"])

        # load model
        if self.model_name == "catboost":
            self.model = CatBoostRegressor()
            self.model.load_model(context.artifacts["model"])
        elif self.model_name in ["rf", "random_forest"]:
            self.model = joblib.load(context.artifacts["model"])
        else:
            raise ValueError(f"Unknown model_name: {self.model_name}")

    def predict(
        self, context: mlflow.pyfunc.PythonModelContext, model_input: pd.DataFrame
    ) -> np.ndarray:  # ty: ignore[invalid-method-override]
        x_scaled = self.scaler.transform(model_input)
        return self.model.predict(x_scaled)
```

### Add the node to pipeline and run
```python
node(
   func=log_to_mlflow,
   inputs=["tuning_results", "training_results", "params:training_pipeline", "params:mlflow"],
   outputs="mlflow_model_uri",
),
```

### Create register_model() node and add it to the Pipeline
**Tell about model registry stages and migration from them to aliases and tags:**
https://github.com/mlflow/mlflow/issues/10336
```python
def register_model(model_uri: str, mlflow_params: dict[str, Any]) -> None:
    """
    Register a model in MLflow and add candidate alias.

    Parameters
    ----------
    model_uri : str
        The MLflow model URI to register.
    mlflow_params : dict[str, Any]
        MLflow config containing 'registered_model_name' and 'model_aliases'.

    Returns
    -------
    str
        The registered model version.
    """
    client = MlflowClient()
    registered_model_name = mlflow_params["registered_model_name"]

    # 1) Register model
    model_info = mlflow.register_model(
        model_uri=model_uri,
        name=registered_model_name,
    )

    version = str(model_info.version)

    # 2) Add alias
    client.set_registered_model_alias(
        name=registered_model_name, 
        alias=mlflow_params["model_aliases"]["candidate"], 
        version=version
    )
    return None
```
### To run, we need to add aliases to the config file
```yaml
mlflow:
  prod_experiment_name: prod_model_training
  registered_model_name: wind_power_predictor
  model_aliases:
    candidate: challenger
    production: champion
```


### Add the node to the pipeline
```python
node(
   func=register_model,
   inputs=["mlflow_model_uri", "params:mlflow"],
   outputs=None,
),
```
Now, we can see the model registered as `Challenger` and ready to become a `Champion` and be used
for inference in Production!


### Promotion of the model:
1. Show the slide about Model Promotion
2. Here's the pseudo code:
```python
# Load mlflow model from registry
# Compute metrics on the test set
# If challenger metrics better, deploy challenger
# If current champion metrics are better, keep champion
```
3. First, we will implement model loading by alias function which we can use both in training and inference.
4. Create `common/mlflow_utils.py`
```python
def load_model_by_alias(registered_model_name: str, alias: str) -> Any:
    """
    Load a model from MLflow model registry by alias.

    Resolves the alias to a model version, then loads that version.

    Parameters
    ----------
    registered_model_name : str
        The name of the registered model in MLflow.
    alias : str
        Model alias (e.g., 'champion', 'challenger').

    Returns
    -------
    Any
        The loaded MLflow pyfunc model. This model can be used directly for
        predictions as it handles scaling internally (if bundled with scaler).
    """
    client = MlflowClient()
    model_version = client.get_model_version_by_alias(registered_model_name, alias)
    model_uri = f"models:/{registered_model_name}/{model_version.version}"
    return mlflow.pyfunc.load_model(model_uri)
```
5. Create `validate_challenger()` Node:
```python
def validate_challenger(
    x_test: pd.DataFrame,
    y_test: pd.Series,
    training_results: dict[str, Any],
    mlflow_params: dict[str, Any]
) -> None:
    """
    Validates candidate model against production and promote if better (lower MAPE).

    Loads champion model from registry using load_model_by_alias, predicts on current
    test set, computes MAPE, and compares with challenger's MAPE.
    Promotes challenger to production if better.

    Parameters
    ----------
    x_test : pd.DataFrame
        Test features (same split as used for challenger).
    y_test : pd.Series
        Test target (same split as used for challenger).
    training_results : dict[str, Any]
        From fit_best_model, contains 'test_metrics' with challenger's test_mape.
    mlflow_params : dict[str, Any]
        MLflow config containing 'registered_model_name' and 'model_aliases'.

    Returns
    -------
    None
        Modifies model aliases in MLflow.
    """
    client = MlflowClient()
    registered_model_name = mlflow_params["registered_model_name"]
    candidate_alias = mlflow_params["model_aliases"]["candidate"]
    production_alias = mlflow_params["model_aliases"]["production"]

    # Load champion model and predict on current test set, compute MAPE
    try:
        champion_model = load_model_by_alias(registered_model_name, alias=production_alias)
        y_pred = champion_model.predict(x_test)
        champion_mape = compute_metrics(y_test, y_pred)["mape"]
    except Exception:
        champion_mape = float("inf")  # No champion exists, promote challenger

    challenger_mape = training_results["test_metrics"]["test_mape"]

    if challenger_mape < champion_mape:
        client.delete_registered_model_alias(registered_model_name, production_alias)
        client.set_registered_model_alias(
            name=registered_model_name,
            alias=production_alias,
            version=client.get_model_version_by_alias(
                registered_model_name, candidate_alias
            ).version,
        )
        client.delete_registered_model_alias(
            registered_model_name, candidate_alias
        )
    return None
```

6. Add the Node in the Pipeline
```python
node(
      func=validate_challenger,
      inputs=[
          "x_test",
          "y_test",
          "training_results",
          "params:mlflow",
          "model_version",
      ],
      outputs=None,
  ),
```


# Inference Pipeline Development
### Create directories
1. Create `src/pipelines/inference`, `__init__.py`, `nodes.py`, `pipeline.py` 

### Create Load Champion Model Node to be explicit
```python
def load_champion_model(mlflow_params: dict[str, Any]) -> Any:
    """
    Load the production (champion) model from MLflow model registry.

    Wrapper that extracts config values and calls load_model_by_alias.

    Parameters
    ----------
    mlflow_params : dict[str, Any]
        MLflow config containing 'registered_model_name' and 'model_aliases'.

    Returns
    -------
    Any
        The loaded production model (MLflow pyfunc model) with scaler bundled.
    """
    registered_model_name = mlflow_params["registered_model_name"]
    production_alias = mlflow_params["model_aliases"]["production"]
    return load_model_by_alias(registered_model_name, alias=production_alias)
```
### Add Node
```python
from kedro.pipeline import Pipeline, node
from .nodes import load_champion_model


def create_pipeline(**kwargs) -> Pipeline:
    """Create the inference pipeline."""
    return Pipeline([
        node(
            func=load_champion_model,
            inputs=["params:mlflow"],
            outputs="champion_model",
        ),
    ])
```

### Add to Pipeline Registry
```python
from kedro.pipeline import Pipeline
from turbine_anomaly_detector.pipelines.feature_eng.pipeline import create_pipeline as create_feature_eng_pipeline
from turbine_anomaly_detector.pipelines.training.pipeline import create_pipeline as create_training_pipeline
from turbine_anomaly_detector.pipelines.inference.pipeline import create_pipeline as create_inference_pipeline

def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    feature_eng_pipeline = create_feature_eng_pipeline()
    training_pipeline = create_training_pipeline()
    inference_pipeline = create_inference_pipeline()

    return {
        "__default__": feature_eng_pipeline + training_pipeline,
        "training": feature_eng_pipeline + training_pipeline,
        "inference": feature_eng_pipeline + inference_pipeline,
    }
```

### Run Kedro Pipeline by Name
```bash
kedro run --pipeline=inference
```

### Note that for now we use the same data as for training. Later, we will change it


### Add `predict` node
```python
def predict(features_data: pd.DataFrame, champion_model: Any) -> pd.DataFrame:
    """
    Make predictions using the champion model on new data.

    Parameters
    ----------
    features_data : pd.DataFrame
        Input features for prediction. Must have the same columns as the
        training data (excluding the target column).
    champion_model : Any
        Loaded champion model (MLflow pyfunc model) that has a `predict` method.

    Returns
    -------
    pd.Series
        Predicted target values for the input features.
    """
    predictions = champion_model.predict(features_data)
    return pd.DataFrame(predictions, columns=["predictions"])
```

### Add to the pipeline
```python
from kedro.pipeline import Pipeline, node
from .nodes import load_champion_model, predict


def create_pipeline(**kwargs) -> Pipeline:
    """Create the inference pipeline."""
    return Pipeline([
        node(
            func=load_champion_model,
            inputs=["params:mlflow"],
            outputs="champion_model",
        ),
        node(
            func=predict,
            inputs=["features_data", "champion_model"],
            outputs="predictions",
        ),
    ])
```

### Create a Kedro Dataset, so that we can use predictions in the Monitoring Pipeline
```yaml
predictions:
  type: pandas.ParquetDataset
  filepath: data/07_model_output/predictions.parquet
```

# Monitoring Pipeline
### Create directories

### Create node `conpute_anomaly_metrics`
```python
"""Monitoring pipeline nodes."""
"""Monitoring pipeline nodes."""
import pandas as pd
import numpy as np

def compute_anomaly_metrics(y_pred: pd.Series, y_true: pd.Series) -> dict[str, float]:
    """
    Compute MAPE metric from predictions and target data.

    Parameters
    ----------
    y_pred : pd.Series
        Predicted values.
    target_data : pd.Series
        Ground truth target values.

    Returns
    -------
    dict[str, float]
        Dictionary containing 'mae', 'rmse', and 'mape' metrics.
    """
    y_true = y_true.values.ravel()
    y_pred = y_pred.values.ravel()
    mape = np.abs(y_true - y_pred) / (y_true + 1e-8) * 100
    return mape
```

### Add node to the pipeline
```python
"""Monitoring pipeline."""
from kedro.pipeline import Pipeline, node
from .nodes import compute_anomaly_metrics


def create_pipeline(**kwargs) -> Pipeline:
    """Create the monitoring pipeline."""
    return Pipeline([
        node(
            func=compute_anomaly_metrics,
            inputs=["predictions", "target_data"],
            outputs="anomaly_metrics",
        ),
    ])
```
### Add to Pipeline Registry
```python
from kedro.pipeline import Pipeline
from turbine_anomaly_detector.pipelines.feature_eng.pipeline import create_pipeline as create_feature_eng_pipeline
from turbine_anomaly_detector.pipelines.training.pipeline import create_pipeline as create_training_pipeline
from turbine_anomaly_detector.pipelines.inference.pipeline import create_pipeline as create_inference_pipeline
from turbine_anomaly_detector.pipelines.monitoring.pipeline import create_pipeline as create_monitoring_pipeline

def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    feature_eng_pipeline = create_feature_eng_pipeline()
    training_pipeline = create_training_pipeline()
    inference_pipeline = create_inference_pipeline()
    monitoring_pipeline = create_monitoring_pipeline()

    return {
        "__default__": feature_eng_pipeline + training_pipeline,
        "training": feature_eng_pipeline + training_pipeline,
        "inference": feature_eng_pipeline + inference_pipeline,
        "monitoring": monitoring_pipeline,
    }
```