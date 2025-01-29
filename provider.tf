provider "google" {
  project     = "autobot-v1-356820"
  region      = var.region
  zone        = "us-central1-c"
  credentials = file(var.credentials_path)
}