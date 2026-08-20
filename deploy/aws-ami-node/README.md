# AlgoView AWS AMI execution appliance

This appliance adds IP-only AWS onboarding without changing the existing
manual Execution IP feature. It carries no shared bootstrap secret. The main
server verifies the AWS-signed EC2 instance identity document before accepting
registration.

## Client flow

1. Launch the published AlgoView ARM64 AMI using `t4g.nano` or `t4g.micro`.
2. Use an RSA key pair for emergency SSH access.
3. Allow TCP `3128` only from the main AlgoView public IP and TCP `22` only
   from the client's administrator IP.
4. Copy the instance public IPv4.
5. In AlgoView select **AWS AMI Node**, paste the IPv4, and save.
6. The agent registers from that IP. AlgoView validates the AWS signature and
   approved AMI ID, verifies proxy egress, and assigns the route automatically.
7. Add the IPv4 to the broker's static-IP settings and complete broker login.

Use an Elastic IP for production because an automatically assigned public IPv4
can change after the instance is stopped and started.

## Build

```bash
packer init deploy/aws-ami-node/algoview-node-arm64.pkr.hcl
packer build \
  -var 'subnet_id=subnet-...' \
  -var 'security_group_id=sg-...' \
  -var 'main_server_url=https://app.sparkstechnologies.co.in' \
  -var 'main_server_ip=MAIN_SERVER_PUBLIC_IP' \
  deploy/aws-ami-node/algoview-node-arm64.pkr.hcl
```

After Packer returns the AMI ID, configure the main server:

```env
AWS_AMI_NODE_ENABLED=True
AWS_AMI_ALLOWED_IDS=ami-generated-by-packer
AWS_AMI_ALLOWED_REGIONS=ap-south-1
AWS_AMI_ALLOWED_ARCHITECTURES=arm64
AWS_AMI_PROXY_PORT=3128
AWS_AMI_CLAIM_TTL_SECONDS=1800
```

The bundled Mumbai DSA certificate comes from AWS's official EC2 instance
identity certificate list. Review that list when adding another AWS Region.
Never place broker credentials, database credentials, Git credentials, SSH
private keys, or client-specific secrets in the image.

`launch-template.yaml` creates a restricted security group and launch template,
forces IMDSv2, uses encrypted gp3 storage, and limits the instance choice to
ARM64-compatible `t4g.nano` or `t4g.micro`.
