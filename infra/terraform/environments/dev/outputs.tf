output "resource_group" {
  description = "Resource group name"
  value       = module.resource_group.name
}

output "web_app_url" {
  description = "Application URL"
  value       = "https://${module.app_service.default_hostname}"
}

output "postgres_fqdn" {
  description = "PostgreSQL host"
  value       = module.postgresql.fqdn
}

output "redis_host" {
  description = "Redis host"
  value       = module.redis.hostname
}
