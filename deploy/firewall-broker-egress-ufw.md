# Broker Egress Firewall Guard

The Django application server must fail closed at the network layer too. Do not
allow the main server to connect directly to broker API hosts. Only execution
nodes or approved proxy endpoints should be reachable.

## UFW Baseline

Replace the example proxy IPs with the approved execution/proxy vendors.

```bash
sudo ufw default deny outgoing
sudo ufw default deny incoming
sudo ufw allow in 22/tcp
sudo ufw allow in 80/tcp
sudo ufw allow in 443/tcp

# Redis / database / internal services, adjust to private CIDR only.
sudo ufw allow out to 10.0.0.0/8

# DNS and NTP.
sudo ufw allow out 53
sudo ufw allow out 123/udp

# Approved proxy / execution-node egress only.
sudo ufw allow out to <APPROVED_PROXY_IPV4> port <PROXY_PORT> proto tcp
sudo ufw allow out to <APPROVED_PROXY_IPV6> port <PROXY_PORT> proto tcp

sudo ufw enable
```

## AWS Security Group / NACL Rule

- Inbound: 80/443 from internet, SSH only from admin IP.
- Outbound: deny all by default.
- Outbound allow only Redis/database private CIDRs, DNS/NTP, and approved
  execution-node/proxy IP:port pairs.

Broker API domains must not be directly reachable from the main application
server. Any successful direct request to a broker API host is a production
incident.
