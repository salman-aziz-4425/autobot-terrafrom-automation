resource "google_pubsub_topic" "topics" {
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
  
  name = "${each.value.tenant_name}_${each.value.function_name}"
}