resource "azurerm_redis_cache" "this" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  capacity            = 0
  family              = "C"
  sku_name            = var.sku_name
  minimum_tls_version = "1.2"
  enable_non_ssl_port = false
  tags                = var.tags
}
