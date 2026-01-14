import os
from huggingface_hub import snapshot_download

# Define model directory
model_dir = "D:/MASrepos/deepagents-langchain/libs/deepagents-web/services/deepagents_data/models"

print(f"Downloading models to {model_dir}...")

try:
    snapshot_download(
        repo_id="opendatalab/PDF-Extract-Kit",
        local_dir=model_dir,
        resume_download=True,
        max_workers=4
    )
    print("Download complete.")
except Exception as e:
    print(f"Download failed: {e}")
