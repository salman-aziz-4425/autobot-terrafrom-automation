terraform {
  backend "gcs" {
    bucket = "autobot_scheduler_cloud_function"
    prefix = "terraform/state"
    credentials = "/Users/salmanaziz/.config/gcloud/application_default_credentials.json"
  }
} 
