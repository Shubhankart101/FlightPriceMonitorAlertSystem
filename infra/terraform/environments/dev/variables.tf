variable "project" {
  description = "Project short name"
  type        = string
  default     = "pulsenotify"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "app_service_plan_sku" {
  description = "App service plan SKU"
  type        = string
  default     = "B1"
}

variable "postgresql_sku" {
  description = "PostgreSQL SKU"
  type        = string
  default     = "B_Standard_B1ms"
}

variable "redis_sku" {
  description = "Redis SKU"
  type        = string
  default     = "Basic"
}

variable "docker_image_name" {
  description = "Application image to deploy"
  type        = string
  default     = "ghcr.io/owner/repo:latest"
}

variable "django_secret_key" {
  description = "Django secret key"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "pulse_db"
}

variable "db_admin_username" {
  description = "Database admin username"
  type        = string
  default     = "pulse_admin"
}

variable "db_admin_password" {
  description = "Database admin password"
  type        = string
  sensitive   = true
}
