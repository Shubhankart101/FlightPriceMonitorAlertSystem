terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.117"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
}

locals {
  name_prefix = "${var.project}-${var.environment}-${random_string.suffix.result}"
  tags = {
    app         = var.project
    environment = var.environment
    managed_by  = "terraform"
  }
}

module "resource_group" {
  source   = "../../modules/resource_group"
  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = local.tags
}

module "app_service_plan" {
  source              = "../../modules/app_service_plan"
  name                = "plan-${local.name_prefix}"
  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  sku_name            = var.app_service_plan_sku
  tags                = local.tags
}

module "postgresql" {
  source              = "../../modules/postgresql"
  name                = "psql-${local.name_prefix}"
  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  database_name       = var.db_name
  admin_username      = var.db_admin_username
  admin_password      = var.db_admin_password
  sku_name            = var.postgresql_sku
  tags                = local.tags
}

module "redis" {
  source              = "../../modules/redis"
  name                = "redis-${local.name_prefix}"
  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  sku_name            = var.redis_sku
  tags                = local.tags
}

module "app_service" {
  source              = "../../modules/app_service"
  name                = "app-${local.name_prefix}"
  location            = module.resource_group.location
  resource_group_name = module.resource_group.name
  service_plan_id     = module.app_service_plan.id
  docker_image_name   = var.docker_image_name
  app_settings = {
    DJANGO_SETTINGS_MODULE = "pulse.settings.production"
    SECRET_KEY             = var.django_secret_key
    DB_ENGINE              = "postgres"
    DB_NAME                = var.db_name
    DB_USER                = var.db_admin_username
    DB_PASSWORD            = var.db_admin_password
    DB_HOST                = module.postgresql.fqdn
    DB_PORT                = "5432"
    CELERY_BROKER_URL      = "rediss://${module.redis.hostname}:${module.redis.ssl_port}/0"
    CELERY_RESULT_BACKEND  = "rediss://${module.redis.hostname}:${module.redis.ssl_port}/0"
    FLIGHT_PRICE_API_URL   = "https://app-${local.name_prefix}.azurewebsites.net/api/flights/price/"
  }
  tags = local.tags
}
