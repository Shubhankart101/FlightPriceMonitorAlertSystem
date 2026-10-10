output "hostname" {
  value       = azurerm_redis_cache.this.hostname
  description = "Redis host name"
}

output "ssl_port" {
  value       = azurerm_redis_cache.this.ssl_port
  description = "Redis SSL port"
}
