# Manual Deployment
### Create DigitalOcean Account

### Add payment method:
- Navigate to Settings → Billing
- Add a credit card or PayPal account
- Required for creating droplets

### Create Project

### Create Droplet for $24

### First time, you need to create SSH key
```bash
ssh-keygen -t ed25519
```

### Then copy it:
```bash
cat ~/.ssh/id_ed25519.pub
```

### Then add to the droplet

## Go to terminal and add:
```bash
ssh root@YOUR_DROPLET_IP
```

### Install Docker
```bash
https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04
```

### Remove `data/01_raw/` from gitignore
```gitignore
# except their sub-folders
!data/**/
!data/01_raw/**
```

### Clone repo, change directory to it and run
```bash
docker compose up --build
```

# Automated CD pipeline
### Show the slide `Continious Delievry (CD). Why?`

### We need to create access token to Dockerhub
1. **Create DockerHub token**
- Go to https://hub.docker.com
- Click your profile (top right)
- Go to Account Settings
- Personal Access Token
- Generate new Token
- Access Token Description - `Anomaly-Detection-CD`
- Access Permission - `Read & Write`
- Copy the token

2. **Add Secrets to GitHub**
- Go to GitHub
- Go to Repository -> Settings -> Secrets and Variables -> Actions -> New Repository Secret
- Secret_1
  - DOCKERHUB_USERNAME = timurbikmukhametov
  - DOCKERHUB_TOKEN -> copy your token

### Now, we need to create a GitHub Action Workflow for the CD pipeline

### Create a cd.yml file under `.github/workflows` folder
```yaml
name: CD

on:
  workflow_run:
    workflows: ["CI"]  # must match your CI workflow name
    types: [completed] # completed does NOT mean successful.

env:
  IMAGE_NAME: turbine-anomaly

jobs:
  build-and-push:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      # Buildx enables advanced Docker builds (caching, multi-platform, and `buildx --push`).
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}:latest
```

### Push the code, check CI and then updated image on DockerHub

### Now, since we deploy the pushed image, we need to update the docker-compose file
Instead of building the image locally from the Dockerfile, we need to pull the image
from DockerHub.

Let's rename the current docker-compose file to `docker-compose.local.yml`

This file we can then still use for local docker containers with
```bash
docker compose -f docker-compose.local.yml up --build
```

### Here's the updated `docker-compose.yml`
Instead of
```yaml
build:
      context: .
      dockerfile: Dockerfile
```
Use
```yaml
image: ${DOCKERHUB_USERNAME}/turbine-anomaly:latest
```
We will need to setup the env variable `DOCKERHUB_USERNAME`


### Now, since we are pushing to the Digital Ocean server, GitHub Actions need to be able to access it
For this, wwe need to add additional secrets to GitHub
- Go to GitHub
- Go to Repository -> Settings -> Secrets and Variables -> Actions -> New Repository Secret
- Secret_1
  - DO_HOST = Droplet ip
  - DO_USER -> root
  - DO_SSH_KEY -> run `cat ~/.ssh/id_ed25519`, copy everything

### Now, add the deploy step to the CD file
```yaml
deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.head_branch == 'main' }} # only deploy on main branch

    steps:
      - name: Deploy to DigitalOcean
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.DO_HOST }}
          username: ${{ secrets.DO_USER }}
          key: ${{ secrets.DO_SSH_KEY }}
          script: |
            set -e
            cd /opt/turbine-anomaly

            export DOCKERHUB_USERNAME=${{ secrets.DOCKERHUB_USERNAME }}
            export KEDRO_VIZ_URI=http://${{ secrets.DO_HOST }}:4141
            export MLFLOW_UI_URI=http://${{ secrets.DO_HOST }}:8080

            docker compose pull
            docker compose up -d --remove-orphans
```

### Env variables
Environment variables are then used in the application and docker compose
```yaml
export DOCKERHUB_USERNAME=${{ secrets.DOCKERHUB_USERNAME }}
export KEDRO_VIZ_URI=http://${{ secrets.DO_HOST }}:4141
export MLFLOW_TRACKING_URI=http://${{ secrets.DO_HOST }}:8080
export MLFLOW_UI_URI=http://${{ secrets.DO_HOST }}:8080
```







## Part 3: Building the Continuous Deployment Pipeline

### Step 1: Understanding the CD Pipeline

The CD pipeline automates:
1. Building Docker image when code changes
2. Pushing image to Docker Hub
3. Deploying to DigitalOcean droplet
4. Pulling latest images and restarting services

### Step 2: Set Up GitHub Secrets

1. **Navigate to GitHub repository:**
   - Go to Settings → Secrets and variables → Actions

2. **Add required secrets:**

   **Docker Hub secrets:**
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: Docker Hub access token
     - Generate at: https://hub.docker.com/settings/security
     - Click "New Access Token"
     - Name: `github-actions`
     - Permissions: Read & Write

   **DigitalOcean secrets:**
   - `DO_HOST`: Your droplet IP address (e.g., `123.45.67.89`)
   - `DO_USER`: SSH username (usually `root`)
   - `DO_SSH_KEY`: Your private SSH key
     - Generate if needed: `ssh-keygen -t ed25519 -C "github-actions"`
     - Copy private key: `cat ~/.ssh/id_ed25519`
     - Add public key to droplet: `ssh-copy-id root@YOUR_DROPLET_IP`

### Step 3: Create CD Workflow File

Create `.github/workflows/cd.yml`:

```yaml
name: CD

on:
  workflow_run:
    workflows: ["CI"]  # must match your CI workflow name
    types: [completed] # completed does NOT mean successful.

env:
  IMAGE_NAME: turbine-anomaly

jobs:
  build-and-push:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      # Buildx enables advanced Docker builds (caching, multi-platform, and `buildx --push`).
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}:latest
```

### Push the created CD and check if the image in DockerHub is updated

### Now, we need to add the deploy part
```yaml
deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.head_branch == 'main' }} #  only deploy on main branch

    steps:
      - name: Deploy to DigitalOcean
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: '${{ secrets.DO_HOST }}'
          username: '${{ secrets.DO_USER }}'
          key: '${{ secrets.DO_SSH_KEY }}'
          script: |
            set -e
            cd turbine-anomaly-detector

            export DOCKERHUB_USERNAME='${{ secrets.DOCKERHUB_USERNAME }}'
            export KEDRO_VIZ_URI='http://${{ secrets.DO_HOST }}:4141'
            export MLFLOW_UI_URI='http://${{ secrets.DO_HOST }}:8080'

            docker compose pull
            docker compose up -d --remove-orphans
```

### We need to make Docker compose down and pull the files with updated Docker compose
This is because Docker makes a copy of you image, it does not copy the files.

### Push the code and check if the updated container runs on Digital Ocean