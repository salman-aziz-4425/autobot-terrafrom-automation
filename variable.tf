variable "functions" {
  description = "List of functions to deploy"
  type = list(object({
    name           = string
    runtime        = string
    memory         = number
    entry_point    = string
    source_archive = string
    frequency      = string
    description    = string
  }))
  default = [
    {
      name           = "bu_extraction"
      runtime        = "python311"
      memory         = 512
      entry_point    = "extract_business_units"
      source_archive = "bu_extraction.zip"
      frequency      = "0 0 1 * *"
      description    = "Business Unit Extraction"
    },
    {
      name           = "campaign_extraction"
      runtime        = "python311"
      memory         = 1024
      entry_point    = "extract_campaigns"
      source_archive = "campaign_extraction.zip"
      frequency      = "*/2 * * * *"
      description    = "Campaign Extraction"
    },
    {
      name           = "customer_contact_extraction"
      runtime        = "python311"
      memory         = 1024
      entry_point    = "extract_cdc_customer_contact"
      source_archive = "customer_contact_extraction.zip"
      frequency      = "*/4 * * * *"
      description    = "Customer Contact Extraction"
      timezone       = "America/Chicago"
    },
    {
      name           = "customer_extraction"
      runtime        = "python311"
      memory         = 1024
      entry_point    = "extract_customers"
      source_archive = "customer_extraction.zip"
      frequency      = "*/3 * * * *"
      description    = "Customer Extraction"
    },
    {
      name           = "customer_information_extraction"
      runtime        = "python311"
      memory         = 2048
      entry_point    = "transform"
      source_archive = "customer_information_extraction.zip"
      frequency      = "*/6 * * * *"
      description    = "Customer Information Extraction"
    },
    {
      name           = "job_type_extraction"
      runtime        = "python311"
      memory         = 512
      entry_point    = "extract_job_types"
      source_archive = "job_type_extraction.zip"
      frequency      = "0 0 1 * *"
      description    = "Job Type Extraction"
    },
    {
      name           = "location_extraction"
      runtime        = "python311"
      memory         = 1024
      entry_point    = "extract_locations"
      source_archive = "location_extraction.zip"
      frequency      = "*/2 * * * *"
      description    = "Location Extraction"
    },
    {
      name           = "membership_extraction"
      runtime        = "python311"
      memory         = 1024
      entry_point    = "extract_memberships"
      source_archive = "membership_extraction.zip"
      frequency      = "*/2 * * * *"
      description    = "Membership Extraction"
    },
    {
      name           = "membership_types_extraction"
      runtime        = "python311"
      memory         = 512
      entry_point    = "extract_membership_types"
      source_archive = "membership_types_extraction.zip"
      frequency      = "0 0 * * 5"
      description    = "Membership Types Extraction"
    },
    {
      name           = "technician_extraction"
      runtime        = "python311"
      memory         = 512
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
  }))
  default = [{
    name = "Yarbrough_and_Sons"
    id   = "469367432"
    }, {
    name = "Absolute Comfort"
    id   = "563439940"
    },
    {
      name = "Alaskan AC Phoenix",
      id   = "408376968"
    },
    {
      name = "Alaskan AC Tucson",
      id   = "385536259"
    }
  ]
}

variable "timezone" {
  description = "GCP Region"
  type        = map(string)
  default = {
    "yarbrough_and_sons" = "America/Chicago"
    "absolute_comfort"   = "America/New_York",
    "alaskan_ac_phoenix" = "America/Phoenix",
    "alaskan_ac_tucson"  = "America/Phoenix"
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


variable "bucket_name" {
  description = "GCS Bucket for function source code"
  type        = string
  default     = "autobot_scheduler_cloud_function"
}
