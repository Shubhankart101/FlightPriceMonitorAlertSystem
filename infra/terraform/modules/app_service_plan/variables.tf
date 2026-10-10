variable "name" {
  description = "App Service plan name"
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

variable "sku_name" {
  description = "Azure App Service plan SKU"
  type        = string
  default     = "B1"
}

variable "tags" {
  description = "Tags applied to resources"
  type        = map(string)
  default     = {}
}
