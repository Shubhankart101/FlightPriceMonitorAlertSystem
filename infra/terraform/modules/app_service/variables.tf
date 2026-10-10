variable "name" {
  description = "Web app name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "service_plan_id" {
  description = "App service plan ID"
  type        = string
}

variable "docker_image_name" {
  description = "Docker image tag (repo/image:tag)"
  type        = string
}

variable "docker_registry_url" {
  description = "Container registry URL"
  type        = string
  default     = "https://ghcr.io"
}

variable "app_settings" {
  description = "Application settings for Django"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Tags applied to resources"
  type        = map(string)
  default     = {}
}
