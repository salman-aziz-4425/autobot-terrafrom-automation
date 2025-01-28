# module "function_storage" {
#   source      = "./modules/function_storage"
#   functions   = var.functions
#   tenants     = var.tenants
#   bucket_name = var.bucket_name
# }

module "pubsub" {
  source    = "./modules/pubsub"
  functions = var.functions
  tenants   = var.tenants
  region    = var.region
}

module "cloud_functions" {
  source    = "./modules/cloud_functions"
  functions = var.functions
  tenants   = var.tenants
  region    = var.region
  depends_on = [module.pubsub]
  # depends_on = [module.function_storage] # Ensure functions are uploaded before creating Cloud Functions
}

module "cloud_scheduler" {
  source            = "./modules/cloud_scheduler"
  functions         = var.functions
  tenants           = var.tenants
  region            = var.region
  pubsub_topic_name = module.pubsub.name
  depends_on        = [module.cloud_functions]
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project     = "autobot-v1-356820"
  region      = var.region
  zone        = "us-central1-c"
  credentials = file(var.credentials_path)
}

resource "null_resource" "check_credentials" {
  provisioner "local-exec" {
    command = "if [ ! -f ${var.credentials_path} ]; then echo 'Credentials file not found at ${var.credentials_path}'; exit 1; fi"
  }
}