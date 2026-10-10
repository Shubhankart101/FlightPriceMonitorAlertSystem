output "default_hostname" {
  value       = azurerm_linux_web_app.this.default_hostname
  description = "Public hostname for the web app"
}

output "id" {
  value       = azurerm_linux_web_app.this.id
  description = "Web app ID"
}
