# Configuration
$PROJECT_ID = "sports-media-protection"
$SERVICE_NAME = "sports-asset-protection"
$REGION = "us-central1"
$IMAGE_TAG = "gcr.io/$PROJECT_ID/$SERVICE_NAME"
$BUCKET_NAME = "sports-media-protection-bucket"

Write-Host "Starting deployment for $SERVICE_NAME in project $PROJECT_ID..." -ForegroundColor Cyan

# 1. Ensure we are in the backend directory
Set-Location backend

# 2. Build and push the image using Cloud Build
Write-Host "Building and pushing container image..." -ForegroundColor Yellow
gcloud builds submit --tag $IMAGE_TAG --project $PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed. Aborting deployment." -ForegroundColor Red
    exit 1
}

# 3. Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
  --image $IMAGE_TAG `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300s `
  --set-env-vars GCS_BUCKET=$BUCKET_NAME `
  --project $PROJECT_ID

Write-Host "Deployment complete!" -ForegroundColor Green

# 4. Get the URL
$URL = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)' --project $PROJECT_ID
Write-Host "Service URL: $URL" -ForegroundColor White
