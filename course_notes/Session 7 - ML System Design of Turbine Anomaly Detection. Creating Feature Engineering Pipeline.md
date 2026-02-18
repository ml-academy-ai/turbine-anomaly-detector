## Feature Engineering Pipeline
As we see in the diagram, for ML pipelines, we will use Kedro. (Present Kedro Slides)

I believe the best way to start learning Kedro is to start using it.

First, we develop a Feature Engineering Pipeline.

1. In `src/turbine_anomaly_detection/pipelines` create feature_eng directory with `__init__.py`


2. Create nodes.py and pipeline.py file. It's NOT the required structure, but this structure 
is easy to follow.


3. Let's start going though our **get_clean_data()** function in from the Notebook04


4. Our first action here is that we filter outliers by the filter by difference. 
Before implementing this step, let's implement a couple of other simpler but common steps
that exist in many pipelines.


5. The first step is renaming data. I often start from the config file and then decide on the way
I want to implement the function (node). So, let's go to the config


6. In config, it's convenient to make the main keys as the pipeline names.
Here's the way we can rename our parameters:


```bash
feature_eng_pipeline:
  rename_columns:
    WindSpeed: "wind_speed"
    WindDirAbs: "wind_dir_abs"
    Power: "power"
    Pitch: "pitch"
    GenRPM: "gen_rpm"
    WindDirRel: "wind_dir_rel"
    NacelTemp: "nacel_temp"
    GenPh1Temp: "gen_phase_temp"
    RotorRPM: "rotor_rpm"
    EnvirTemp: "envir_temp"
    GearOilTemp: "gear_oil_temp"
    GearBearTemp: "gear_bear_temp"
```

**7. Now, let's use it to create a node:**
```python
def rename_columns(df: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    """
    Rename columns in a dataframe.
    """
    return df.rename(columns=columns)
```

**8. Let's finally create our first pipeline!**
```python
node(
    func=rename_columns,
    inputs=["df_train", "params:feature_eng_pipeline.rename_columns"],
    outputs="renamed_data",
)
```

**10. Now, we need to create df_train in the data catalog. Then Kedro will automatically load this
data for us.**
```bash
df_train:
  type: pandas.ParquetDataset
  filepath: data/01_raw/df_train.parquet
```

**11. Now, to run the pipeline, we need to go to the PipelineRegistry, register the pipeline and run**
```python
from kedro.pipeline import Pipeline
from turbine_anomaly_detector.pipelines.feature_eng.pipeline import create_pipeline

def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    feature_eng_pipeline = create_pipeline()

    return {
        "__default__": feature_eng_pipeline
    }
```
Potentially, we will need to run: uv add kedro-datasets


**12. Another operation we need to drop Timestamps column. Potentially, we can later do that 
when we use the production data loading, but for now, we can just drop the column. For that, let's create
drop_column node:**

```python
def drop_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Drop columns in a dataframe.
    """
    return df.drop(columns=columns)
```

Now, add `drop_columns: ["Timestamps"]` to the config file and add the node to Pipeline.

**13. Now, it gets more interesting. We are now ready to start cleaning the data. Let's look at the
`get_clean_data()` function.**

First, we need to implement `filter_by_difference`. 

Copy this function to nodes. We can see that for now it takes ONE column and ONE value.

However, for us it will be easy to specify all the thresholds and then put it to the function.

So, we need to modify it. First, let's prepare the config.

```bash
diff_outliers_thresholds:
    wind_speed: 12
    wind_dir_abs: 70
    power: 200
    pitch: 12
    gen_rpm: 450
    wind_dir_rel: 9
    nacel_temp: 40
    gen_phase_temp: 40
    rotor_rpm: 20
    envir_temp: 17
    gear_oil_temp: 20
    gear_bear_temp: 35
```

```python
def remove_diff_outliers(df: pd.DataFrame, diff_thresholds: dict[str, float]) -> pd.DataFrame:
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
Note that we will be using the same feature engineering pipeline for both training and inference.

In the Notebook, for convenience, we removed the outliers only in the training set because we wanted to 
compute the error on the original signal.

In the pipeline, we can just use the original data with outliers to compute the error.

So not to change the code for training and inference pipelines, we can do the same cleaning and just use different
dataframe if we want to compute the error. For instance, we can later use `dropped_columns_data` dataset to compute
the error between our prediction and the actual non-filtered value.

**14. Next, we need to apply the mean filter. We apply this to all the features except `Power`.
We copy the code and similarly make it applicable for the dict of columns and values.**

First, prepare the config:

```bash
smooth_signal:
    columns: [
      wind_speed, 
      wind_dir_abs, 
      pitch, 
      gen_rpm, 
      wind_dir_rel, 
      nacel_temp, 
      gen_phase_temp, 
      rotor_rpm, 
      envir_temp, 
      gear_oil_temp, 
      gear_bear_temp
    ]
    window: 3
    method: mean
```

Then, the function will be:
```python
def smooth_signal(df: pd.DataFrame, columns: str, window: int, method: str = "mean") -> pd.DataFrame:
    df_smoothed = df.copy()

    for col in columns:
        if method == "mean":
            df_smoothed[col] = df_smoothed[col].rolling(
                window=window, min_periods=1, center=False
            ).mean()

        elif method == "median":
            df_smoothed[col] = df_smoothed[col].rolling(
                window=window, min_periods=1, center=False
            ).median()

        else:
            raise ValueError("method must be 'mean' or 'median'")

    return df_smoothed
```
Then, add the node:
```python
node(
    func=smooth_signal,
    inputs=[
        "removed_outliers_data", 
        "params:feature_eng_pipeline.smooth_signal.columns",
        "params:feature_eng_pipeline.smooth_signal.window", 
        "params:feature_eng_pipeline.smooth_signal.method"
    ],
    outputs="smoothed_data",
),
```

**15. Now, we need to add lagged features**
Also, need to turn it to have inputs as a dict and make it more generic, so that for each feature
we can specify the lags.

First, let's add the config.
```python
lag_features:
    gen_rpm: [1, 2, 3]
    gen_phase_temp: [1, 2, 3]
    wind_speed: [1, 2, 3]
```

Then, we copy the function from the Notebook and modify it like this:
```python
def add_lag_features(df: pd.DataFrame, lags_dict: dict[str, list[int]], drop_na=False) -> pd.DataFrame:
    df_result = df.copy()

    # Create lag features
    for col, lags in lags_dict.items():
        for lag in lags:
            df_result[f"{col}_lag{lag}"] = df_result[col].shift(lag)

    if drop_na:
        return df_result.dropna()
    else:
        return df_result.bfill()  # Backward fill NaNs
```

Then, we add a node:
```python
node(
    func=add_lag_features,
    inputs=[
        "smoothed_data", 
        "params:feature_eng_pipeline.lag_features"
    ],
    outputs="lagged_data",
),
```

**16. Now, we add rolling_stats_features. We need to modify it to accept a dict**
First, we add a config:
```python
rolling_features: # just an example, we can add more stats and windows
gen_rpm:
  stats: [median]
  windows: [3, 6]
gen_phase_temp:
  stats: [mean, max]
  windows: [3, 6]
wind_speed:
  stats: [max]
  windows: [3, 6]
wind_dir_abs:
  stats: [max]
  windows: [3, 6]
wind_dir_rel:
  stats: [max]
  windows: [3, 6]
pitch:
  stats: [max]
  windows: [3, 6]
rotor_rpm:
  stats: [max]
  windows: [3, 6]
```

Then, we modify the function:
```python
def add_rolling_features(
    df: pd.DataFrame,
    stats_window_dict: dict[str, dict[str, list]],
    drop_na=False,
) -> pd.DataFrame:
    df_result = df.copy()

    for col in stats_window_dict.keys():
        for window in stats_window_dict[col]["windows"]:
            rolling = df_result[col].rolling(window)
            for stat in stats_window_dict[col]["stats"]:
                if stat == "mean":
                    df_result[f"{col}_roll{window}_mean"] = rolling.mean()
                elif stat == "median":
                    df_result[f"{col}_roll{window}_median"] = rolling.median()
                elif stat == "std":
                    df_result[f"{col}_roll{window}_std"] = rolling.std()
                elif stat == "min":
                    df_result[f"{col}_roll{window}_min"] = rolling.min()
                elif stat == "max":
                    df_result[f"{col}_roll{window}_max"] = rolling.max()
                elif stat == "skew":
                    df_result[f"{col}_roll{window}_skew"] = rolling.skew()
                elif stat == "kurt":
                    df_result[f"{col}_roll{window}_kurt"] = rolling.kurt()
    if drop_na:
        return df_result.dropna()
    else:
        return df_result.bfill()  # Backward fill NaNs
```

Then, we add a node:
```python
node(
    func=add_rolling_features,
    inputs=[
        "lagged_data", 
        "params:feature_eng_pipeline.rolling_features"
    ],
    outputs="rolled_stats_data",
),
])
```

**17. Finally, later it will be convinient, as an output from the Feature Eng. Pipeline to
have featurs and target as separate Dataframes.**

So, let's create one more node for it.

```python
def get_features_and_target(
    df: pd.DataFrame, target: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Get the features and target from the dataframe.
    """
    x = df.drop(columns=target).copy()
    y = df[[target]].copy()
    return x, y
```

In config, let's add:
```python
target: 'power'
```
And then, let's add a node:
```python
node(
    func=get_features_and_target,
    inputs=[
        "rolled_stats_data", 
        "params:feature_eng_pipeline.target"
    ],
    outputs=["features_data", "target_data"],
    ),
```

**18. We can now add kedro-viz and vizualize the pipeline**
Add `uv add kedro-viz` and run `kedro-viz`
