# 🏢 后端部署指南

本指南将引导您完成 WHartTest 后端服务的生产环境部署。系统已改为使用API方式调用嵌入模型，无需本地下载模型文件。

## 📊 数据库配置

系统支持两种数据库：
- **PostgreSQL**（默认）：生产环境推荐，支持高并发
- **SQLite**：适合本地开发和小规模部署

### 使用 PostgreSQL（默认）

1. **安装 PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

2. **创建数据库和用户**
```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 在 PostgreSQL 中执行
CREATE DATABASE wharttest;
CREATE USER wharttest_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE wharttest TO wharttest_user;
\q
```

3. **配置环境变量**
```bash
# 设置数据库类型为 PostgreSQL
export DATABASE_TYPE=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=wharttest
export POSTGRES_USER=wharttest_user
export POSTGRES_PASSWORD=your_secure_password
```

4. **执行数据库迁移**
```bash
python manage.py migrate
```

### 使用 SQLite（本地开发）

如需使用 SQLite，设置环境变量：
```bash
# 切换到 SQLite
export DATABASE_TYPE=sqlite
# SQLite 数据库文件位置
export DATABASE_PATH=/path/to/db.sqlite3
```

### Docker 部署时切换数据库

Docker 默认使用 PostgreSQL。如需使用 SQLite，编辑 `.env` 文件：
```yaml
# 使用 SQLite（本地开发）
DATABASE_TYPE=sqlite
```

---

### 🛠️ 后端部署 (以 Ubuntu 为例)


#### 1. 系统准备
首先，安装 `uv`，一个先进的 Python 包管理器。
```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 将 uv 添加到当前会话的 PATH
source $HOME/.cargo/env

# 注意：为了永久生效，请将 `source $HOME/.cargo/env` 添加到您的 shell 配置文件中 (如 ~/.bashrc 或 ~/.zshrc)
```

#### 2. 克隆项目
```bash
git clone <your-repo-url>
cd WHartTest_Django
```

#### 3. 创建并激活虚拟环境
使用 `uv` 创建并激活一个基于 Python 3.12 的虚拟环境。
```bash
# 使用 Python 3.12 创建虚拟环境
uv venv --python 3.11 

# 激活虚拟环境
source .venv/bin/activate
```

#### 4. 安装依赖
使用 `uv` 高效地安装项目依赖。
```bash
uv pip sync -r requirements.txt
```

#### 5. 数据库迁移和超级用户创建
```bash
# 执行数据库迁移
python manage.py migrate
# Windows执行数据库迁移
uv run python WHartTest_Django/manage.py migrate
# 创建超级管理员
python manage.py createsuperuser
# Windows创建超级管理员
uv run WHartTest_Django/manage.py createsuperuser
```

#### 6. 启动服务
```bash
# 使用 Gunicorn 启动 Django 应用
gunicorn wharttest_django.wsgi:application --bind 0.0.0.0:8000 --workers 4
# Windows启动Django服务
uv run python WHartTest_Django/manage.py runserver 0.0.0.0:8000
```

#### 6. 收集静态文件
在生产环境中，静态文件（如 CSS, JavaScript, 图片）应由 Nginx 等 Web 服务器直接提供，以获得更好的性能。`collectstatic` 命令会将项目所有应用中的静态文件收集到 `STATIC_ROOT` 指定的单个目录中，以便于部署。
```bash
python manage.py collectstatic --noinput
```

#### 7. 使用 Gunicorn 启动服务
```bash
# 安装 gunicorn
pip install gunicorn

# 启动服务
gunicorn wharttest_django.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  --preload
```
*   `--preload` 会在启动时预加载模型，减少首次请求的延迟。


## 🔍 部署验证

### 1. 验证 API 连接
启动服务后，检查日志输出，确认嵌入模型 API 连接正常。
```log
🚀 正在初始化嵌入模型API...
✅ 嵌入模型API连接成功
🧪 API测试成功，服务正常
🤖 向量存储管理器初始化完成:
   ✅ 实际使用的嵌入模型: API嵌入服务
```

### 2. API 健康检查
```bash
# 检查项目 API 是否正常 (需要有效的 JWT Token)
curl -X GET http://your-domain.com/api/projects/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. 知识库功能测试
通过 API 创建一个知识库，上传文档并进行搜索，验证整个流程是否正常。

## ✅ 生产环境检查清单

- [ ] `DEBUG` 设置为 `False`
- [ ] `SECRET_KEY` 已更换为强密钥
- [ ] 使用 `Gunicorn` 或其他 WSGI 服务器
- [ ] 配置 `Nginx` 作为反向代理
- [ ] 数据库已从 SQLite 切换到 `PostgreSQL`
- [ ] 嵌入模型 API 已配置并连接正常
- [ ] 静态文件已通过 `collectstatic` 收集并由 Nginx 服务
- [ ] `SSL/TLS` 证书已配置，强制 HTTPS
- [ ] 防火墙已启用，只开放必要端口
- [ ] 备份策略已制定（数据库和用户上传文件）
- [ ] 日志记录和监控已配置