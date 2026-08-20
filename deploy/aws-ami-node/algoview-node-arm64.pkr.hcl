packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = ">= 1.3.0"
    }
  }
}

variable "region" { default = "ap-south-1" }
variable "subnet_id" { type = string }
variable "security_group_id" { type = string }
variable "main_server_url" { type = string }
variable "main_server_ip" { type = string }

source "amazon-ebs" "algoview_arm64" {
  region            = var.region
  instance_type     = "t4g.micro"
  ssh_username      = "ubuntu"
  subnet_id         = var.subnet_id
  security_group_id = var.security_group_id
  ami_name          = "algoview-execution-node-arm64-{{timestamp}}"
  source_ami_filter {
    filters = {
      name                = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-arm64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    owners      = ["099720109477"]
    most_recent = true
  }
  tags = {
    Name = "AlgoView Execution Node ARM64"
    Role = "algoview-execution-node"
  }
}

build {
  sources = ["source.amazon-ebs.algoview_arm64"]
  provisioner "file" {
    source      = "deploy/aws-ami-node/"
    destination = "/tmp/algoview-ami-node"
  }
  provisioner "shell" {
    environment_vars = [
      "ALGOVIEW_MAIN_SERVER_URL=${var.main_server_url}",
      "ALGOVIEW_MAIN_SERVER_IP=${var.main_server_ip}",
      "ALGOVIEW_AMI_PROXY_PORT=3128",
      "ALGOVIEW_AMI_AGENT_VERSION=1",
    ]
    execute_command = "sudo -E bash '{{.Path}}'"
    script          = "deploy/aws-ami-node/install.sh"
  }
}
