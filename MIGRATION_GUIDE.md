# 🚀 从 Railway 迁移到 EC2 实战指南 (定制版)

本文档是为您当前 EC2 环境定制的详细操作手册。我们将配置 GitHub Actions，实现您在本地 Mac 写代码，推送到 GitHub 后，EC2 服务器自动更新并重启服务。

## 📋 准备工作

请确保您手头有以下信息和文件：
1.  **密钥文件**：`moltbot.pem` (位于您的 Mac 本地)
2.  **服务器地址**：`ec2-18-140-58-172.ap-southeast-1.compute.amazonaws.com`
3.  **登录用户**：`ubuntu`

---

## 🛠️ 第一步：配置 GitHub 仓库 (一次性设置)

我们需要把连接服务器的“钥匙”交给 GitHub，这样它才能帮您部署。

1.  **打开 GitHub 仓库页面**。
2.  点击顶部的 **Settings** (设置) 选项卡。
3.  在左侧菜单栏找到 **Secrets and variables** -> 点击 **Actions**。
4.  点击绿色的 **New repository secret** 按钮，依次添加以下 3 个变量（注意大小写）：

### 变量 1: `EC2_HOST`
*   **Name**: `EC2_HOST`
*   **Secret**: `ec2-18-140-58-172.ap-southeast-1.compute.amazonaws.com`
*   *(点击 Add secret 保存)*

### 变量 2: `EC2_USERNAME`
*   **Name**: `EC2_USERNAME`
*   **Secret**: `ubuntu`
*   *(点击 Add secret 保存)*

### 变量 3: `EC2_SSH_KEY` (最关键的一步)
我们需要获取 `moltbot.pem` 的完整文本内容。
1.  在您的 Mac 终端中，进入存放 `moltbot.pem` 的目录。
2.  运行以下命令将密钥内容复制到剪贴板：
    ```bash
    cat moltbot.pem | pbcopy
    ```
3.  回到 GitHub 页面：
    *   **Name**: `EC2_SSH_KEY`
    *   **Secret**: (直接粘贴，即 Command + V)
    *   *内容应该以 `-----BEGIN RSA PRIVATE KEY-----` 开头，以 `-----END RSA PRIVATE KEY-----` 结尾。*
4.  *(点击 Add secret 保存)*

---

## 💻 第二步：初始化服务器环境

我们需要登录服务器，安装必要软件并下载代码。

### 1. 登录服务器
在您的 Mac 终端执行：
```bash
ssh -o ServerAliveInterval=60 -i "moltbot.pem" ubuntu@ec2-18-140-58-172.ap-southeast-1.compute.amazonaws.com
```

### 2. 安装 Docker 和 Git (如果尚未安装)
登录成功后，复制并运行以下命令：
```bash
# 更新软件源
sudo apt-get update

# 安装 Docker, Docker Compose 和 Git
sudo apt-get install -y docker.io docker-compose git

# 启动 Docker 并设置开机自启
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户加入 docker 组 (这样运行 docker 命令就不需要 sudo 了)
sudo usermod -aG docker $USER
```
> **注意**：执行完最后一步后，建议**断开 SSH 连接并重新登录**，以便权限生效。
> *   退出命令：`exit`
> *   重新连接：(使用上面的 ssh 命令再次登录)

### 3. 克隆代码并配置
重新登录后：
```bash
# 1. 确保在主目录
cd ~

# 2. 克隆您的代码 (将 URL 替换为您仓库的实际地址)
# 如果是私有仓库，通过 HTTPS 克隆可能需要输入 GitHub 账号密码(Token)
# 或者您可以配置 SSH Key，这里假设是公开仓库或您已配置好
git clone https://github.com/您的GitHub用户名/viba_sticker.git

# 3. 进入项目目录
cd viba_sticker

# 4. 创建环境变量文件
nano .env
```
在打开的编辑器中，粘贴您的配置信息（Discord Token 等）：
```ini
DISCORD_TOKEN=您的Token粘贴在这里
GEMINI_API_KEY=您的Key粘贴在这里
# 其他需要的变量...
```
*   **保存退出方法**：按 `Ctrl + O`，回车确认，然后按 `Ctrl + X`。

---

## 🚀 第三步：验证并启动

在服务器上测试一下是否能正常运行：

```bash
# 构建并启动容器
docker-compose up -d --build

# 查看运行状态
docker-compose ps
```
如果看到状态是 `Up`，说明部署成功！

---

## 🎉 完成！后续如何更新？

以后您只需要在 **本地 Mac** 上操作：

1.  修改代码。
2.  提交推送到 GitHub：
    ```bash
    git add .
    git commit -m "更新了新功能"
    git push origin main
    ```
3.  **这就够了！** 
    *   GitHub Actions 会自动检测到更新。
    *   它会自动登录您的 EC2。
    *   它会拉取最新代码并重启 Docker 容器。

您可以去 GitHub 仓库的 **Actions** 标签页查看部署进度。

---

## ❓ 常用维护命令 (在服务器上执行)

*   **查看机器人日志**：
    ```bash
    cd ~/viba_sticker
    docker-compose logs -f --tail=100
    ```
*   **手动重启**：
    ```bash
    cd ~/viba_sticker
    docker-compose restart
    ```
*   **停止服务**：
    ```bash
    cd ~/viba_sticker
    docker-compose down
    ```
