output "fqdn" {
  value       = azurerm_postgresql_flexible_server.this.fqdn
  description = "PostgreSQL server FQDN"
}

output "database_name" {
  value       = azurerm_postgresql_flexible_server_database.this.name
  description = "Database name"
}
