#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="sports-asset-protection"
REGION="us-central1"
IMAGE_TAG="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "Starting deployment for $SERVICE_NAME in project $PROJECT_ID..."

# 1. Build and push the image using Cloud Build
# We run this from the backend directory
cd backend
gcloud builds submit --tag $IMAGE_TAG

# 2. Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_TAG \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300s \
  --set-env-vars GCS_BUCKET="sports-media-guard-demo"

echo "✅ Deployment complete!"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
