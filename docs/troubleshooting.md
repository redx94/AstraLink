# Troubleshooting Guide for AstraLink

This guide covers common issues that users may encounte while setting up and deploying AstraLink.

## Common Issues & Solutions

- Not able to start services: 
	- Solution: Ensure you use correct `docker compose` configuration. Run `docker-compose config` to check for errors.

- System deployment fails on Fly.io: 
	- Solution: Check that the `Volumes` section in the `fly.toml` file matches your system resource configuration.

- Blockchain module errors:
	- Solution: Check that your environment variables closely match the requirements in the `requirements.txt` file. Resolve any missing packages.