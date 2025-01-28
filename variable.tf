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
  }))
  default = [
    {
      name           = "bu_extraction"
      runtime        = "python311"
      memory         = "512MB"
      entry_point    = "extract_business_units"
      source_archive = "bu_extraction.zip"
      frequency      = "0 0 1 * *"
      description    = "Business Unit Extraction"
    },
    {
      name           = "campaign_extraction"
      runtime        = "python311"
      memory         = "512MB"
      entry_point    = "extract_campaigns"
      source_archive = "campaign_extraction.zip"
      frequency      = "*/2 * * * *"
      description    = "Campaign Extraction"
    },   
    {
      name = "customer_contact_extraction"
      runtime = "python311"
      memory = "512MB"
      entry_point = "extract_cdc_customer_contact"
      source_archive = "customer_contact_extraction.zip"
      frequency = "*/4 * * * *"
      description = "Customer Contact Extraction"
      timezone = "America/Chicago"
    },
    {
      name           = "customer_extraction"
      runtime        = "python311"
      memory         = "512MB"
      entry_point    = "extract_customers"
      source_archive = "customer_extraction.zip"
      frequency      = "*/3 * * * *"
      description    = "Customer Extraction"
      },
    {
      name           = "customer_information_extraction"
      runtime        = "python311"
      memory         = "512MB"
      entry_point    = "transform"
      source_archive = "customer_information_extraction.zip"
      frequency      = "*/6 * * * *"
      description    = "Customer Information Extraction"
    },
    {
      name           = "job_type_extraction"
      runtime        = "python311"
      memory         = "512MB"
      entry_point    = "extract_job_types"
      source_archive = "job_type_extraction.zip"
      frequency      = "0 0 1 * *"
      description    = "Job Type Extraction"
      },
    {
      name           = "location_extraction"
      runtime        = "python311"
      memory         = "512MB"
      entry_point    = "extract_locations"
      source_archive = "location_extraction.zip"
      frequency      = "*/2 * * * *"
      description    = "Location Extraction"
    },
    {
      name           = "membership_extraction"
      runtime        = "python311"
      memory         = "512MB"
      entry_point    = "extract_memberships"
      source_archive = "membership_extraction.zip"
      frequency      = "*/2 * * * *"
      description    = "Membership Extraction"
    },
    {
      name           = "membership_types_extraction"
      runtime        = "python311"
      memory         = "512MB"
      entry_point    = "extract_membership_types"
      source_archive = "membership_types_extraction.zip"
      frequency      = "0 0 * * 5"
      description    = "Membership Types Extraction"
    },
    {
      name           = "technician_extraction"
      runtime        = "python311"
      memory         = "512MB"
      entry_point    = "extract_technician"
      source_archive = "technician_extraction.zip"
      frequency      = "0 0 1 * *"
      description    = "Technician Extraction"
    },
    
  ]
}

variable "tenants" {
  description = "List of tenants with their IDs"
  type = list(object({
    name = string
    id   = string
    timezone = string
  }))
  default = [{
    name = "Yarbrough_and_Sons"
    id   = "469367432"
    timezone = "America/Chicago"
  },{
    name = "Absolute Comfort"
    id   = "563439940"
    timezone = "America/New_York"
  }
  ]
}

variable "timezone" {
  description = "GCP Region"
  type        = map(string)
  default     = {
    "yarbrough_and_sons" = "America/Chicago"
    "absolute_comfort" = "America/New_York"
  }
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "credentials_path" {
  description = "Path to GCP credentials file"
  type        = string
  default     = "/Users/salmanaziz/.config/gcloud/application_default_credentials.json"
}

variable "pubsub_topic_name" {
  description = "PubSub Topic Name"
  type        = map(string)
  default     = {
    "Yarbrough_and_Sons_bu_extraction" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_bu_extraction"
    "Yarbrough_and_Sons_customer_contact_extraction" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_customer_contact_extraction"
    "Yarbrough_and_Sons_campaign_extraction" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_campaign_extraction"
    "Yarbrough_and_Sons_contact_extraction" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_contact_extraction"
    "Yarbrough_and_Sons_customer_extraction" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_customer_extraction"
    "Yarbrough_and_Sons_customer_information" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_customer_information"
    "Yarbrough_and_Sons_job_type_extraction" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_job_type_extraction"
    "Yarbrough_and_Sons_location_extraction" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_location_extraction"
    "Yarbrough_and_Sons_membership_extraction" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_membership_extraction"
    "Yarbrough_and_Sons_membership_types_extraction" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_membership_types_extraction"
    "Yarbrough_and_Sons_technician_extraction" = "projects/autobot-v1-356820/topics/Yarbrough_and_Sons_technician_extraction",
    "Absolute_Comfort_bu_extraction" = "projects/autobot-v1-356820/topics/Absolute_Comfort_bu_extraction",
    "Absolute_Comfort_campaign_extraction" = "projects/autobot-v1-356820/topics/Absolute_Comfort_campaign_extraction",
    "Absolute_Comfort_customer_contact_extraction" = "projects/autobot-v1-356820/topics/Absolute_Comfort_customer_contact_extraction",
    "Absolute_Comfort_customer_extraction" = "projects/autobot-v1-356820/topics/Absolute_Comfort_customer_extraction",
    "Absolute_Comfort_customer_information" = "projects/autobot-v1-356820/topics/Absolute_Comfort_customer_information",
    "Absolute_Comfort_job_type_extraction" = "projects/autobot-v1-356820/topics/Absolute_Comfort_job_type_extraction",
    "Absolute_Comfort_location_extraction" = "projects/autobot-v1-356820/topics/Absolute_Comfort_location_extraction",
    "Absolute_Comfort_membership_extraction" = "projects/autobot-v1-356820/topics/Absolute_Comfort_membership_extraction",
    "Absolute_Comfort_membership_types_extraction" = "projects/autobot-v1-356820/topics/Absolute_Comfort_membership_types_extraction",
    "Absolute_Comfort_technician_extraction" = "projects/autobot-v1-356820/topics/Absolute_Comfort_technician_extraction"
  }
}

variable "bucket_name" {
  description = "GCS Bucket for function source code"
  type        = string
  default     = "autobot_scheduler_cloud_function"
}
