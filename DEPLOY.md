# Deployment Guide (EC2 + Docker)

This project is deployed on an AWS EC2 instance using Docker. It uses GitHub Actions for automated deployment (CI/CD).

## Architecture

- **Platform**: AWS EC2 (Ubuntu)
- **Runtime**: Docker Container (`python:3.10-slim`)
- **Orchestration**: Docker Compose (`restart: always` ensures high availability)
- **CI/CD**: GitHub Actions (Push to `main` -> Auto-deploy to EC2)

## Prerequisites

- AWS EC2 Instance (Ubuntu)
- Docker & Docker Compose installed on the server
- GitHub Repository Secrets configured:
  - `EC2_HOST`: Public DNS/IP of the instance
  - `EC2_USER`: `ubuntu`
  - `EC2_SSH_KEY`: Content of your `.pem` key file
  - `DISCORD_TOKEN`: Discord bot token used in production
  - `GEMINI_API_KEY`: Gemini API key used in production

## Server Maintenance

To manage the bot manually, SSH into the server:

```bash
ssh -o ServerAliveInterval=60 -i "your-key.pem" ubuntu@your-ec2-host
```

### Common Commands

| Action | Command |
| :--- | :--- |
| **Check Status** | `docker ps` (Look for `viba_sticker`) |
| **View Logs** | `docker logs -f viba_sticker --tail 100` |
| **Restart Bot** | `docker restart viba_sticker` |
| **Stop Bot** | `docker stop viba_sticker` |
| **Manual Update** | `git pull && docker compose up -d --build` |

## Environment Variables

The bot reads environment variables from a `.env` file in the project root on the server (`~/viba_sticker/.env`).
That file is generated during deployment by GitHub Actions from repository Secrets, and should not be committed to the repository for production use.

**Required Variables:**
```env
DISCORD_TOKEN=your_token_here
GEMINI_API_KEY=your_gemini_key_here
```

**Optional Variables:**
```env
GEMINI_TEXT_MODEL=gemini-3-pro-preview
GEMINI_IMAGE_MODEL=gemini-3.1-flash-image-preview
GEMINI_IMAGE_MODEL_FALLBACK=gemini-2.5-flash-image
```

## GitHub Secrets Setup

In your GitHub repository, go to `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`, then add:

- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_KEY`
- `DISCORD_TOKEN`
- `GEMINI_API_KEY`

After these are set, the deploy workflow will:

1. SSH into the EC2 host
2. Run `git pull origin main`
3. Recreate `~/viba_sticker/.env` from GitHub Secrets
4. Run `docker-compose down --remove-orphans`
5. Run `docker-compose up -d --build`

## CI/CD Workflow

The deployment workflow is defined in [.github/workflows/deploy.yml](.github/workflows/deploy.yml).

**Triggers:**
1. **Push to `main`**: Automatically deploys the latest code.
2. **Manual Trigger**: Go to GitHub Actions -> `Deploy to EC2` -> `Run workflow`.

**What it does:**
1. Connects to EC2 via SSH.
2. Pulls the latest code from GitHub.
3. Regenerates the server-side `.env` file from GitHub Secrets.
4. Rebuilds the Docker image.
5. Restarts the container (with minimal downtime).
