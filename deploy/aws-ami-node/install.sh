#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

install -d -m 0755 /etc/algoview-node /var/lib/algoview-node
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tinyproxy ca-certificates python3
install -m 0755 /tmp/algoview-ami-node/algoview_ami_agent.py /usr/local/bin/algoview-ami-agent
install -m 0644 /tmp/algoview-ami-node/algoview-ami-agent.service /etc/systemd/system/algoview-ami-agent.service

cat >/etc/algoview-node/agent.env <<EOF
ALGOVIEW_MAIN_SERVER_URL=${ALGOVIEW_MAIN_SERVER_URL:?required}
ALGOVIEW_MAIN_SERVER_IP=${ALGOVIEW_MAIN_SERVER_IP:?required}
ALGOVIEW_AMI_PROXY_PORT=${ALGOVIEW_AMI_PROXY_PORT:-3128}
ALGOVIEW_AMI_AGENT_VERSION=${ALGOVIEW_AMI_AGENT_VERSION:-1}
EOF
chmod 0600 /etc/algoview-node/agent.env

systemctl daemon-reload
systemctl enable tinyproxy.service algoview-ami-agent.service
systemctl stop algoview-ami-agent.service || true
rm -rf /var/lib/cloud/instances/* /var/lib/cloud/instance
rm -f /etc/ssh/ssh_host_*
truncate -s 0 /etc/machine-id
rm -f /var/lib/dbus/machine-id
rm -f /root/.bash_history /home/ubuntu/.bash_history
