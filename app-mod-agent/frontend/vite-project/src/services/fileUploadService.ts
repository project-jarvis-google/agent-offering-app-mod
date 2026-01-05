const GCS_UPLOAD_ENDPOINT = 'https://app-mod-agent-backend-428871167882.us-central1.run.app/upload-file';

/**
 * Uploads a file to the GCS bucket via the backend API and returns the GCS URI.
 * The backend response format is expected to be: 
 * {"gsutil_uri": "gs://bucket-name/path/to/file.pdf", "content_type": "..."}
 * @param fileObject The File object to upload.
 * @returns A promise that resolves to the full GCS URI string.
 */
export async function uploadFileToGCS(fileObject: File): Promise<string> {
  const formData = new FormData();
  
  formData.append('file', fileObject, fileObject.name);

  const response = await fetch(GCS_UPLOAD_ENDPOINT, { 
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorDetails = `Status: ${response.status} ${response.statusText}`;
    try {
        const errorBody = await response.json();
        errorDetails += `. Details: ${JSON.stringify(errorBody)}`;
    } catch (e) {
        console.error("Failed to parse error response body as JSON.", e);
    }
    throw new Error(`File upload failed: ${errorDetails}`);
  }

  const fileMetadata = await response.json(); 

  if (!fileMetadata || typeof fileMetadata.gsutil_uri !== 'string') {
      throw new Error(`Invalid response format from upload API. Expected 'gsutil_uri' field.`);
  }

  const gcsUri = fileMetadata.gsutil_uri;
  
  return gcsUri; 
}

export default uploadFileToGCS;