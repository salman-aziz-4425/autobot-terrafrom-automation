variable "functions" {
  description = "List of functions to deploy"
  type = list(object({
    name            = string
    runtime         = string
    memory          = string
    entry_point     = string
    source_archive  = string
    frequency       = string
    description     = string
    timezone        = string
  }))
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "tenants" {
  description = "List of tenants with their IDs"
  type = list(object({
    name = string
    id   = string
  }))
  default = [{
    name = "Yarbrough_and_Sons"
    id   = "469367432"
  }]
}

variable "pubsub_topic_name" {
  description = "PubSub Topic Name"
  type        = map(string)
  default     = {
    "Yarbrough_and_Sons_bu_extraction" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_bu_extraction"
    "Yarbrough_and_Sons_campaign_extraction" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_campaign_extraction"
  }
}