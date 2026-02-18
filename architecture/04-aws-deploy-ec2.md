
### `docs/04-aws-deploy-ec2.md`
```md
# AWS Deploy (EC2)

## 1) EC2
- Ubuntu 22.04
- SG inbound:
  - SSH 22: My IP
  - TCP 8501: My IP (or temporary 0.0.0.0/0 for demo)

## 2) Server prep
```bash
sudo apt update -y
sudo apt install -y python3-pip python3-venv unzip
