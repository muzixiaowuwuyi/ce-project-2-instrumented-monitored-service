#!/bin/bash

# ==============================================================================
# EC2 Node Post-Pull Initialization & Boot Script
# Location: app/deploy.sh
# ==============================================================================

# 1. 升级系统软件源并安装最基础的依赖环境
sudo apt update -y
sudo apt install python3 python3-pip python3-venv gnupg software-properties-common curl unzip jq -y

# 2. 安装官方最新的 Terraform 二进制文件（用于处理 IaC 逻辑）
if ! command -v terraform &> /dev/null; then
    wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
    sudo apt update -y && sudo apt install terraform -y
fi

# 3. 运行 Terraform 状态对齐
# 假设你的 terraform 文件夹和 app 文件夹在同一级目录下 (即：项目根目录/terraform)
if [ -d "../terraform" ]; then
    cd "../terraform"
    terraform init
    terraform apply -auto-approve
    cd - > /dev/null
fi

# 4. 切换到应用目录，创建并激活独立的 Python 虚拟环境
cd "$(dirname "${BASH_SOURCE[0]}")"
python3 -m venv .venv
source .venv/bin/activate

# 5. 升级 venv 内部的 pip 并安装依赖包
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# 6. 在后台安静地启动守护进程 server.py，并将所有输出灌入 server.log
if [ -f "server.py" ]; then
    # 使用 nohup 确保你退出 SSH 终端后，Flask 服务依然在后台死死驻留
    nohup python3 server.py > server.log 2>&1 &
    echo "Success: Application server has been daemonized in the background."
else
    echo "Error: server.py not found!"
    exit 1
fi