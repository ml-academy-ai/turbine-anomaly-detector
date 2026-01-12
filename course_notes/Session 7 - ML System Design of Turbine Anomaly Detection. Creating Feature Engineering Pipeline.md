## Feature Engineering Pipeline
As we see in the diagram, for ML pipelines, we will use Kedro. (Present Kedro Slides)

I believe the best way to start learning Kedro is to start using it.

First, we develop a Feature Engineering Pipeline.









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





In the pipelines directory, create FTI pipeline folders, pipelines, and nodes .py files
Create Feature Engineering pipeline
Prepare local testing datasets in a separate notebook - 05 - Local Data Preparation.
Start going step-by-step through get_clean_data()
Copy remove_diff_outliers() to nodes
Modify the function to take only a dict with thresholds
Also, mention that we would usually want to rename data, so let’s make this function rename_data().
Add this to the pipeline
Create dataset: input_df (show how to check which datasets are available: https://docs.kedro.org/projects/kedro-datasets/en/kedro-datasets-5.1.0/api/kedro_datasets.pandas.ParquetDataset.html)
Go to pipeline_registry and modify it
Make kedro run
Also, configure debugger in PyCharm:
Module name: kedro
Parameters: run
Working directory: <project_root>

Add drop_columns() node
Add smooth_signal() function, change for multi-features, kedro run
Add lagged_features:
change so that each feature has a lag
kedro run
run in debug to check
Add add_rolling_features() function, change the function so that for each feat I can add stat and window
Add get_features_and_target() function, add this to the pipeline

