Run the service locally using uvicorn app.main:app --reload to verify operations.


PROJECT_ID=$(gcloud config get-value project) && \
gcloud run deploy iw-ingestion-svc \
		--source . \
		--env-vars-file=./.env \
		--memory "4Gi" \
		--project agents-stg \
		--region "us-central1" \
		--allow-unauthenticated \
		--port 8080