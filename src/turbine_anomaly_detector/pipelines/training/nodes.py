import pandas as pd
from typing import Any
import optuna
from .utils import objective, eval_model

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