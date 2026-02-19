### Introduce CI with slides
- `Conitinous Integration. Why?`
- `How Continuous Integration (CI) Works?`
- `Main CI Frameworks`

### What is GitHub Actions?

- GitHub Actions is a CI/CD platform that allows you to automate workflows directly in your GitHub repository. 
- Workflows are defined in YAML files stored in `.github/workflows/`.

## Setting Up Your First GitHub Actions Workflow

### Step 1: Create Workflow Directory

1. Create folder `.github`
2. Create folder `workflows`
3. Create file `ci.yml`
4. Ask 'Cursor':
```yaml
Write a GitHub Actions CI pipeline for my project.

Use push to main trigger

Use jobs: lint-and-type and test

Use github actions checkout repos where possible.
```

4. Copy and paste to the web editor.

### Understanding the Workflow

Let's break down each part:

**1. Workflow name and triggers:**
```yaml
name: CI
on:
  push:
    branches: [main]
```
- The workflow runs on every push to the `main` branch

**2. Job definition:**

Run this job on a Linux virtual machine runner using the latest Ubuntu image.
```yaml
jobs:
  lint-and-type:
    runs-on: ubuntu-latest
```

**3. Checkout code:**
When a job starts:
- The runner is a fresh empty VM
- It does NOT contain your repository code
```yaml
- uses: actions/checkout@v4
```

So `actions/checkout`:
- Connects to your GitHub repo
- Clones the repository
- Checks out the correct commit/branch
- Makes the code available in the runner filesystem

After that, your steps can access the code.

**4. If Python is after uv, put Python above like**

This step installs Python
```yaml
jobs:
  lint-and-type:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
```

**5. Install uv:**
If uv is not installed with pip, change to:
```yaml
- name: Install uv
  run: pip install uv
```

Do the same for tests.

**6. Sync dependencies:**
```yaml
- name: Sync dependencies
  run: uv sync --dev
```
- Installs all project dependencies (including dev dependencies)

**7. Quality checks:**
```yaml
- name: Lint with Ruff
  run: uv run ruff check .
```
- Runs linting checks

```yaml
- name: Enforce formatting with Ruff
  run: uv run ruff format --check .
```
- Checks that code is properly formatted (doesn't modify, just checks)

```yaml
- name: Type checking
  run: uv run ty check src tests
```
- Runs type checking

### Give comments about the test part

### Commit and Push in the repo directly

### Go and check the `Actions` table

### If we see errors with mlflow
1. Add this
```yaml
[tool.ruff.lint.isort]
# Force mlflow to be grouped with the other third-party libraries
known-third-party = ["mlflow"]
# Ensures a consistent category order
section-order = ["future", "standard-library", "third-party", "first-party", "local-folder"]
```
2. Run
```bash
ruff check . --fix
```