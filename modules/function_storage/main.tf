resource "google_storage_bucket_object" "functions" {
  for_each = {
    for pair in flatten([
      for function in var.functions : [
        for tenant in var.tenants : {
          function_name = function.name
          tenant_name   = replace(tenant.name, " ", "_")
          function     = function
        }
      ]
    ]) : "${pair.tenant_name}_${pair.function_name}" => pair
  }

  name   = "${each.value.function_name}.zip" 
  bucket = var.bucket_name
  source = "${path.root}/functions/${each.value.tenant_name}_${each.value.function_name}.zip"

  content_type = "application/zip"
  metadata = {
    content_hash = filemd5("${path.root}/functions/${each.value.tenant_name}_${each.value.function_name}.zip")
  }
}

output "function_urls" {
  value = { for k, v in google_storage_bucket_object.functions : k => v.media_link }
} 