module "function_storage" {
  source      = "./modules/function_storage"
  functions   = var.functions
  tenants     = var.tenants
  bucket_name = var.bucket_name
}

module "pubsub" {
  source     = "./modules/pubsub"
  functions  = var.functions
  tenants    = var.tenants
  region     = var.region
  depends_on = [module.function_storage]
}

module "cloud_functions" {
  source     = "./modules/cloud_functions"
  functions  = var.functions
  tenants    = var.tenants
  region     = var.region
  depends_on = [module.pubsub, module.function_storage]
}

module "cloud_scheduler" {
  source     = "./modules/cloud_scheduler"
  functions  = var.functions
  tenants    = var.tenants
  region     = var.region
  depends_on = [module.cloud_functions]
  timezone   = var.timezone
}




resource "null_resource" "check_credentials" {
  provisioner "local-exec" {
    command = "if [ ! -f ${var.credentials_path} ]; then echo 'Credentials file not found at ${var.credentials_path}'; exit 1; fi"
  }
}
