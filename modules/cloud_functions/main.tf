resource "google_cloudfunctions_function" "functions" {
  for_each = {
    for pair in flatten([
      for function in var.functions : [
        for tenant in var.tenants : {
          function_name = function.name
          tenant_name   = replace(tenant.name, " ", "_")
          tenant_id     = tenant.id
          function     = function
        }
      ]
    ]) : "${pair.tenant_name}_${pair.function_name}" => pair
  }
  
  name                  = "${each.value.tenant_name}_${each.value.function_name}"
  runtime               = each.value.function.runtime
  available_memory_mb   = tonumber(replace(each.value.function.memory, "MB", ""))
  source_archive_bucket = "autobot_scheduler_cloud_function"
  source_archive_object = "${each.value.tenant_name}_${each.value.function_name}.zip"
  entry_point          = each.value.function.entry_point
  region               = var.region

  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = "projects/autobot-v1-356820/topics/${each.key}"
  }

  environment_variables = {
    TENANT_IDS = each.value.tenant_id
  }
}

