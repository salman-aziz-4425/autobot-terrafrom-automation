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
  default = [
    {
      name           = "bu_extraction"
      runtime        = "python311"
      memory         = "512MB"
      entry_point    = "extract_business_units"
      source_archive = "bu_extraction.zip"
      frequency      = "0 0 1 * *"
      description    = "Business Unit Extraction"
      timezone       = "America/Chicago"
    },
    {
      name           = "campaign_extraction"
      runtime        = "python311"
      memory         = "512MB"
      entry_point    = "extract_campaigns"
      source_archive = "campaign_extraction.zip"
      frequency      = "*/2 * * * *"
      description    = "Campaign Extraction"
      timezone       = "America/Chicago"
    }
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
  }]
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


