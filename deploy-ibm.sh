#!/bin/bash
# Deploy to IBM Cloud Code Engine

echo "🚀 Deploying to IBM Cloud Code Engine..."

# Login to IBM Cloud (will prompt for SSO)
ibmcloud login --sso -r us-south

# Target your resource group
ibmcloud target -g Default

# Create or select Code Engine project
ibmcloud ce project create --name data-gov-api || ibmcloud ce project select --name data-gov-api

# Create secrets for environment variables (one-time setup)
ibmcloud ce secret create --name watsonx-env \
  --from-env-file .env || echo "Secret already exists"

# Build and deploy the application
ibmcloud ce application create \
  --name data-gov-api \
  --build-source . \
  --strategy dockerfile \
  --port 8000 \
  --min-scale 0 \
  --max-scale 5 \
  --cpu 0.5 \
  --memory 1G \
  --env-from-secret watsonx-env \
  || ibmcloud ce application update \
      --name data-gov-api \
      --build-source . \
      --strategy dockerfile

echo "✅ Deployment complete!"
echo "🌐 Your API URL:"
ibmcloud ce application get --name data-gov-api --output url
