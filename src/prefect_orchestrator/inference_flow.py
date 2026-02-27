import os
import sys
import tomllib
from pathlib import Path

from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from prefect import flow, task

# Add src directory to path before imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))
sys.path.append(str(project_root))

# Change to project directory so relative paths resolve correctly
os.chdir(project_root)


@task(name="run_inference_pipeline", log_prints=True)
def run_inference_pipeline(env: str = "local") -> None:
    """Run the Kedro inference pipeline programmatically."""
    with open(project_root / "pyproject.toml", "rb") as f:
        package_name = tomllib.load(f)["tool"]["kedro"]["package_name"]

    configure_project(package_name)
    bootstrap_project(project_root)

    with KedroSession.create(project_path=project_root, env=env) as session:
        session.run(pipeline_name="inference")


@flow(name="inference_flow", log_prints=True)
def inference_flow():
    run_inference_pipeline()


if __name__ == "__main__":
    inference_flow()
