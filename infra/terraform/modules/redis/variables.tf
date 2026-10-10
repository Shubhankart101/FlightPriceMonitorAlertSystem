variable "name" {
  description = "Redis cache name"
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
  description = "Redis SKU"
  type        = string
  default     = "Basic"
}

variable "tags" {
  description = "Tags applied to resources"
  type        = map(string)
  default     = {}
}
