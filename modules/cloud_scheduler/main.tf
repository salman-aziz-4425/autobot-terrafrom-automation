resource "google_cloud_scheduler_job" "schedulers" {
  for_each = {
    for pair in flatten([
      for function in var.functions : [
        for tenant in var.tenants : {
          function_name = function.name
          tenant_name   = replace(lower(tenant.name), " ", "_")
          tenant_id     = tenant.id
          function     = function
        }
      ]
    ]) : "${pair.tenant_name}_${pair.function_name}" => pair
  }

  name        = "${each.value.tenant_name}_${each.value.function_name}"
  description = each.value.function.description
  schedule    = each.value.function.frequency
  time_zone   = lookup(var.timezone, each.value.tenant_name)
  region      = var.region

  pubsub_target {
    topic_name = "projects/autobot-v1-356820/topics/${each.key}"
    data       = base64encode(jsonencode({ "tenant_id" = each.value.tenant_id }))
  }
}

output "names" {
  value = { for k, v in google_cloud_scheduler_job.schedulers : k => v.name }
}

output "ids" {
  value = { for k, v in google_cloud_scheduler_job.schedulers : k => v.id }
}