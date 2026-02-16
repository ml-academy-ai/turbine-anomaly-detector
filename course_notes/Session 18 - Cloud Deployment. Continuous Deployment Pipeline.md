# Session 18: Cloud Deployment and Continuous Deployment Pipeline

## Overview

This session covers deploying your ML application to the cloud using DigitalOcean and automating the deployment process with a Continuous Deployment (CD) pipeline. You'll learn how to:

- Set up a DigitalOcean account and create a droplet
- Manually deploy your application to the cloud
- Build a CD pipeline using GitHub Actions
- Automate Docker image building and deployment
- Configure SSH access and secrets management

## Prerequisites

- GitHub repository with your ML application
- Docker Hub account
- Basic understanding of SSH and Linux commands
- GitHub Actions knowledge (from Session 14)

## Part 1: Setting Up DigitalOcean

### Step 1: Create DigitalOcean Account

1. **Sign up for DigitalOcean:**
   - Go to https://www.digitalocean.com
   - Click "Sign Up" and create an account
   - Verify your email address

2. **Add payment method:**
   - Navigate to Settings → Billing
   - Add a credit card or PayPal account
   - Required for creating droplets

### Step 2: Create a Droplet

1. **Navigate to Create Droplet:**
   - Click "Create" → "Droplets" in the DigitalOcean dashboard

2. **Choose configuration:**
   - **Image**: Ubuntu 22.04 (LTS) x64
   - **Plan**: Basic plan, Regular Intel with SSD
   - **CPU**: 2 vCPUs (minimum recommended)
   - **Memory**: 4 GB RAM (minimum recommended)
   - **Storage**: 80 GB SSD (adjust based on data size)
   - **Datacenter region**: Choose closest to your users

3. **Authentication:**
   - **SSH keys**: Add your SSH public key (recommended)
   - Or use password authentication (less secure)

4. **Finalize:**
   - **Hostname**: `ml-app-wind-draft` (or your preferred name)
   - Click "Create Droplet"

5. **Wait for provisioning:**
   - Droplet will be ready in 1-2 minutes
   - Note the IP address (e.g., `123.45.67.89`)

### Step 3: Configure Firewall

1. **Navigate to Networking → Firewalls:**
   - Click "Create Firewall"

2. **Add inbound rules:**
   - **HTTP (80)**: Allow from all sources
   - **HTTPS (443)**: Allow from all sources
   - **Custom (5001)**: Allow from all sources (MLflow)
   - **Custom (8050)**: Allow from all sources (App UI)
   - **Custom (4141)**: Allow from all sources (Kedro Viz)
   - **SSH (22)**: Allow from your IP only (for security)

3. **Apply to droplet:**
   - Select your droplet
   - Click "Create Firewall"

### Step 4: Set Up SSH Access

1. **Get your droplet IP:**
   - From DigitalOcean dashboard, copy the IP address

2. **Test SSH connection:**
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

3. **If using SSH keys:**
   ```bash
   ssh -i ~/.ssh/your_key root@YOUR_DROPLET_IP
   ```

4. **First-time setup:**
   - Update system packages:
     ```bash
     apt update && apt upgrade -y
     ```

## Part 2: Manual Deployment to DigitalOcean

### Step 1: Install Docker on Droplet

1. **SSH into your droplet:**
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

2. **Install Docker:**
   ```bash
   # Install prerequisites
   apt-get update
   apt-get install -y ca-certificates curl gnupg lsb-release

   # Add Docker's official GPG key
   mkdir -p /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

   # Set up repository
   echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
     $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

   # Install Docker Engine
   apt-get update
   apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

   # Verify installation
   docker --version
   docker compose version
   ```

3. **Start Docker service:**
   ```bash
   systemctl start docker
   systemctl enable docker
   ```

### Step 2: Clone Repository

1. **Create application directory:**
   ```bash
   mkdir -p /opt/ml-app-wind-draft
   cd /opt/ml-app-wind-draft
   ```

2. **Clone your repository:**
   ```bash
   # If using HTTPS (requires GitHub token)
   git clone https://github.com/YOUR_USERNAME/ml-app-wind-draft.git .

   # Or if using SSH (requires SSH key setup)
   git clone git@github.com:YOUR_USERNAME/ml-app-wind-draft.git .
   ```

3. **Verify files:**
   ```bash
   ls -la
   # Should see: docker-compose.yml, Dockerfile, etc.
   ```

### Step 3: Set Up Environment Variables

1. **Create `.env` file:**
   ```bash
   cd /opt/ml-app-wind-draft
   nano .env
   ```

2. **Add environment variables:**
   ```bash
   DOCKERHUB_USERNAME=your-dockerhub-username
   MLFLOW_UI_URI=http://YOUR_DROPLET_IP:5001
   KEDRO_VIZ_URI=http://YOUR_DROPLET_IP:4141
   MLFLOW_TRACKING_URI=http://mlflow:5001
   ```

3. **Save and exit:**
   - Press `Ctrl+X`, then `Y`, then `Enter`

### Step 4: Create Required Directories

1. **Create data and MLflow directories:**
   ```bash
   mkdir -p /opt/ml-app-wind-draft/data
   mkdir -p /opt/ml-app-wind-draft/mlflow
   mkdir -p /opt/ml-app-wind-draft/conf
   ```

2. **Set permissions:**
   ```bash
   chmod -R 755 /opt/ml-app-wind-draft/data
   chmod -R 755 /opt/ml-app-wind-draft/mlflow
   ```

### Step 5: Copy Configuration Files

1. **Copy data files (if needed):**
   ```bash
   # If you have data files, copy them to /opt/ml-app-wind-draft/data/01_raw/
   # You can use scp from your local machine:
   # scp -r data/01_raw/* root@YOUR_DROPLET_IP:/opt/ml-app-wind-draft/data/01_raw/
   ```

2. **Verify configuration:**
   ```bash
   ls -la /opt/ml-app-wind-draft/conf/base/
   # Should see: parameters.yml, catalog.yml
   ```

### Step 6: Build and Push Docker Image Locally (Optional)

If you want to test the image first:

1. **Log in to Docker Hub:**
   ```bash
   docker login
   # Enter your Docker Hub username and password
   ```

2. **Build image:**
   ```bash
   cd /opt/ml-app-wind-draft
   docker build -t YOUR_DOCKERHUB_USERNAME/ml-app-wind-draft:latest .
   ```

3. **Push image:**
   ```bash
   docker push YOUR_DOCKERHUB_USERNAME/ml-app-wind-draft:latest
   ```

### Step 7: Run Docker Compose

1. **Pull latest images:**
   ```bash
   cd /opt/ml-app-wind-draft
   export DOCKERHUB_USERNAME=your-dockerhub-username
   export MLFLOW_UI_URI=http://YOUR_DROPLET_IP:5001
   export KEDRO_VIZ_URI=http://YOUR_DROPLET_IP:4141
   docker compose pull
   ```

2. **Start all services:**
   ```bash
   docker compose up -d
   ```

3. **Check service status:**
   ```bash
   docker compose ps
   ```

4. **View logs:**
   ```bash
   # All services
   docker compose logs

   # Specific service
   docker compose logs app-ui

   # Follow logs
   docker compose logs -f
   ```

### Step 8: Verify Deployment

1. **Check services are running:**
   ```bash
   docker compose ps
   # All services should show "Up" status
   ```

2. **Test endpoints:**
   - MLflow UI: http://YOUR_DROPLET_IP:5001
   - App UI: http://YOUR_DROPLET_IP:8050
   - Kedro Viz: http://YOUR_DROPLET_IP:4141

3. **Check service logs for errors:**
   ```bash
   docker compose logs app-ml-train
   docker compose logs app-ml-inference
   docker compose logs app-ui
   ```

### Step 9: Run Training Manually

1. **Start training service:**
   ```bash
   docker compose up app-ml-train
   ```

2. **Wait for training to complete:**
   - Check logs: `docker compose logs -f app-ml-train`
   - Training should complete and save model to MLflow

3. **Start inference and streaming:**
   ```bash
   docker compose up -d app-ml-inference
   docker compose up -d app-stream-data
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
    workflows: ["CI"]  # Trigger after CI workflow completes
    types:
      - completed
  push:
    tags:
      - 'v*.*.*'  # Trigger on version tags
  workflow_dispatch:  # Allow manual trigger

env:
  IMAGE_NAME: ml-app-wind-draft

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ secrets.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=registry,ref=${{ secrets.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}:latest
          cache-to: type=inline

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')
    
    steps:
      - name: Deploy to DigitalOcean
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.DO_HOST }}
          username: ${{ secrets.DO_USER }}
          key: ${{ secrets.DO_SSH_KEY }}
          script: |
            cd /opt/ml-app-wind-draft
            export DOCKERHUB_USERNAME=${{ secrets.DOCKERHUB_USERNAME }}
            export KEDRO_VIZ_URI=http://${{ secrets.DO_HOST }}:4141
            export MLFLOW_UI_URI=http://${{ secrets.DO_HOST }}:5001
            docker compose pull
            docker compose up -d
```

### Step 4: Understanding the CD Workflow

**Workflow triggers:**
- After CI workflow completes successfully
- On version tags (e.g., `v1.0.0`)
- Manual trigger via GitHub Actions UI

**Build job:**
1. Checks out code
2. Sets up Docker Buildx
3. Logs in to Docker Hub
4. Extracts metadata (tags)
5. Builds and pushes Docker image

**Deploy job:**
1. Runs only on `main` branch or version tags
2. SSH into DigitalOcean droplet
3. Navigates to application directory
4. Sets environment variables
5. Pulls latest images
6. Restarts services with `docker compose up -d`

### Step 5: Test the CD Pipeline

1. **Make a change to your code:**
   ```bash
   # On your local machine
   git checkout -b test-cd
   # Make a small change (e.g., update README)
   git add .
   git commit -m "Test CD pipeline"
   git push origin test-cd
   ```

2. **Merge to main:**
   - Create pull request
   - Merge after CI passes

3. **Monitor deployment:**
   - Go to GitHub → Actions tab
   - Watch CD workflow run
   - Check logs for errors

4. **Verify deployment:**
   - SSH into droplet: `ssh root@YOUR_DROPLET_IP`
   - Check services: `docker compose ps`
   - View logs: `docker compose logs -f`

### Step 6: Manual Deployment Trigger

You can also trigger deployment manually:

1. **Go to GitHub Actions:**
   - Navigate to Actions tab
   - Select "CD" workflow
   - Click "Run workflow"
   - Select branch and click "Run workflow"

## Part 4: Advanced CD Pipeline Configuration

### Step 1: Add Health Checks

Update `.github/workflows/cd.yml` to add health check after deployment:

```yaml
  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')
    
    steps:
      - name: Deploy to DigitalOcean
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.DO_HOST }}
          username: ${{ secrets.DO_USER }}
          key: ${{ secrets.DO_SSH_KEY }}
          script: |
            cd /opt/ml-app-wind-draft
            export DOCKERHUB_USERNAME=${{ secrets.DOCKERHUB_USERNAME }}
            export KEDRO_VIZ_URI=http://${{ secrets.DO_HOST }}:4141
            export MLFLOW_UI_URI=http://${{ secrets.DO_HOST }}:5001
            docker compose pull
            docker compose up -d

      - name: Health check
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.DO_HOST }}
          username: ${{ secrets.DO_USER }}
          key: ${{ secrets.DO_SSH_KEY }}
          script: |
            sleep 10
            docker compose ps
            curl -f http://localhost:8050 || exit 1
```

### Step 2: Add Rollback Capability

Create a rollback workflow `.github/workflows/rollback.yml`:

```yaml
name: Rollback

on:
  workflow_dispatch:
    inputs:
      tag:
        description: 'Docker image tag to rollback to'
        required: true
        type: string

jobs:
  rollback:
    runs-on: ubuntu-latest
    steps:
      - name: Rollback on DigitalOcean
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.DO_HOST }}
          username: ${{ secrets.DO_USER }}
          key: ${{ secrets.DO_SSH_KEY }}
          script: |
            cd /opt/ml-app-wind-draft
            export DOCKERHUB_USERNAME=${{ secrets.DOCKERHUB_USERNAME }}
            export KEDRO_VIZ_URI=http://${{ secrets.DO_HOST }}:4141
            export MLFLOW_UI_URI=http://${{ secrets.DO_HOST }}:5001
            docker compose pull
            docker tag ${{ secrets.DOCKERHUB_USERNAME }}/ml-app-wind-draft:${{ github.event.inputs.tag }} ${{ secrets.DOCKERHUB_USERNAME }}/ml-app-wind-draft:latest
            docker compose up -d
```

### Step 3: Add Deployment Notifications

Add Slack/Discord notifications to CD workflow:

```yaml
      - name: Notify deployment
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployment to DigitalOcean ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
        if: always()
```

## Part 5: Monitoring and Maintenance

### Step 1: Monitor Service Health

1. **Set up monitoring script on droplet:**
   ```bash
   nano /opt/ml-app-wind-draft/monitor.sh
   ```

2. **Add monitoring logic:**
   ```bash
   #!/bin/bash
   cd /opt/ml-app-wind-draft
   
   # Check if services are running
   if ! docker compose ps | grep -q "Up"; then
     echo "Services are down! Restarting..."
     docker compose up -d
   fi
   
   # Check disk space
   df -h | awk '$5 > 80 {print "Warning: Disk usage > 80%"}'
   ```

3. **Make executable and add to crontab:**
   ```bash
   chmod +x /opt/ml-app-wind-draft/monitor.sh
   crontab -e
   # Add: */5 * * * * /opt/ml-app-wind-draft/monitor.sh
   ```

### Step 2: Log Management

1. **Set up log rotation:**
   ```bash
   nano /etc/logrotate.d/docker-compose
   ```

2. **Add configuration:**
   ```
   /opt/ml-app-wind-draft/logs/*.log {
     daily
     rotate 7
     compress
     delaycompress
     notifempty
     missingok
   }
   ```

### Step 3: Backup Strategy

1. **Create backup script:**
   ```bash
   nano /opt/ml-app-wind-draft/backup.sh
   ```

2. **Add backup logic:**
   ```bash
   #!/bin/bash
   BACKUP_DIR="/opt/backups"
   DATE=$(date +%Y%m%d_%H%M%S)
   
   mkdir -p $BACKUP_DIR
   
   # Backup data directory
   tar -czf $BACKUP_DIR/data_$DATE.tar.gz /opt/ml-app-wind-draft/data
   
   # Backup MLflow artifacts
   tar -czf $BACKUP_DIR/mlflow_$DATE.tar.gz /opt/ml-app-wind-draft/mlflow
   
   # Keep only last 7 days of backups
   find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
   ```

3. **Schedule daily backups:**
   ```bash
   chmod +x /opt/ml-app-wind-draft/backup.sh
   crontab -e
   # Add: 0 2 * * * /opt/ml-app-wind-draft/backup.sh
   ```

## Part 6: Troubleshooting

### Issue 1: SSH Connection Failed

**Error:** `Error: connect ECONNREFUSED`

**Solutions:**
- Verify droplet IP is correct
- Check firewall allows SSH from GitHub Actions IPs
- Verify SSH key is correctly added to secrets
- Test SSH manually: `ssh root@YOUR_DROPLET_IP`

### Issue 2: Docker Compose Command Not Found

**Error:** `docker compose: command not found`

**Solution:**
- Ensure Docker Compose plugin is installed on droplet
- Run: `apt-get install docker-compose-plugin`

### Issue 3: Permission Denied on Directories

**Error:** `Permission denied: /opt/ml-app-wind-draft/data`

**Solution:**
```bash
chmod -R 755 /opt/ml-app-wind-draft/data
chmod -R 755 /opt/ml-app-wind-draft/mlflow
```

### Issue 4: Services Not Starting

**Error:** Services show as "Exited" in `docker compose ps`

**Solution:**
- Check logs: `docker compose logs`
- Verify environment variables are set
- Check disk space: `df -h`
- Verify Docker Hub credentials

### Issue 5: Image Pull Failed

**Error:** `Error pulling image`

**Solution:**
- Verify Docker Hub credentials in secrets
- Check image exists: `docker pull YOUR_USERNAME/ml-app-wind-draft:latest`
- Verify network connectivity on droplet

### Issue 6: Port Already in Use

**Error:** `Bind for 0.0.0.0:5001 failed: port is already allocated`

**Solution:**
```bash
# Find process using port
lsof -i :5001

# Stop existing containers
docker compose down

# Restart services
docker compose up -d
```

## Part 7: Best Practices

### 1. Security

- Use SSH keys instead of passwords
- Restrict firewall to allow only necessary ports
- Use GitHub secrets for sensitive data
- Regularly update system packages
- Use non-root user for services (if possible)

### 2. Resource Management

- Monitor droplet resource usage
- Set up alerts for high CPU/memory usage
- Use appropriate droplet size for your workload
- Implement log rotation to manage disk space

### 3. Deployment Strategy

- Test deployments on staging environment first
- Use version tags for production deployments
- Implement rollback procedures
- Monitor deployments closely after release

### 4. Backup and Recovery

- Regular backups of data and MLflow artifacts
- Test backup restoration procedures
- Keep backups in separate location
- Document recovery procedures

### 5. Monitoring

- Set up health checks
- Monitor service logs
- Track resource usage
- Set up alerts for failures

## Summary and Key Concepts

### What You've Learned

1. **DigitalOcean Setup**: Creating account, droplet, and firewall configuration
2. **Manual Deployment**: Installing Docker, cloning repo, setting up environment, running services
3. **CD Pipeline**: Building automated deployment with GitHub Actions
4. **SSH Configuration**: Setting up secure access for automated deployments
5. **Monitoring and Maintenance**: Health checks, backups, and log management

### Key Takeaways

- **Manual deployment** helps understand the process before automation
- **CD pipeline** automates building and deployment on code changes
- **GitHub Secrets** securely store sensitive credentials
- **SSH keys** enable secure automated access to servers
- **Monitoring** ensures services stay healthy in production

### Next Steps

- Set up staging environment for testing
- Implement blue-green deployments
- Add monitoring and alerting (e.g., Prometheus, Grafana)
- Set up automated backups
- Consider using Kubernetes for orchestration
- Implement canary deployments for gradual rollouts

