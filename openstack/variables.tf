# ----- Авторизация в OpenStack -----

variable "auth_url" {
  description = "OpenStack auth URL, например https://keystone.example.com:5000/v3"
  type        = string
}

variable "tenant_name" {
  description = "Имя проекта (tenant)"
  type        = string
}

variable "user_name" {
  description = "Имя пользователя OpenStack"
  type        = string
}

variable "password" {
  description = "Пароль пользователя OpenStack"
  type        = string
}

variable "region" {
  description = "Регион OpenStack"
  type        = string
  default     = "RegionOne"
}

# ----- Параметры ВМ -----

variable "image_name" {
  description = "Имя образа (как в Horizon, например ubuntu-22.04)"
  type        = string
}

variable "flavor_name" {
  description = "Flavor для ВМ"
  type        = string
  default     = "m1.medium"   # как на твоём скрине: 1 vCPU, 2GB RAM, 20GB
}

variable "network_name" {
  description = "Имя сети для подключения ВМ"
  type        = string
  default     = "sutdents-net"  # как на твоём скрине
}

# Открытый SSH-ключ, который будет добавлен как keypair
variable "public_ssh_key" {
  description = "Публичный SSH-ключ, одна строка ssh-rsa ..."
  type        = string
}