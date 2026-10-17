# RAGFlow 本地部署手册（Windows + Docker Desktop）

> **适用版本**：RAGFlow `v0.27.2`（最新稳定版）
>
> **适用环境**：Windows 11 + Docker Desktop 4.x + WSL 2
>
> **文档状态**：第一步交付。**本文档只描述步骤，尚未在本机执行 `docker compose pull/up`**；仅执行过 `docker compose config` 语法校验。实际部署属于第二步。

## 1. 版本与配置来源

| 项目 | 值 |
| --- | --- |
| RAGFlow | `v0.27.2` |
| 上游 tag commit | `a024bea0cd93f39e6652a42bf84dd20c55bc560b` |
| Docker 镜像 | `infiniflow/ragflow:v0.27.2` |
| Elasticsearch | `8.11.3` |
| MySQL | `8.0.40` |
| Valkey | `8` |
| 对象存储 | `pgsty/silo`（MinIO 兼容，镜像版本由官方 compose 固定） |
| Compose 文件 | `docs/ragflow/docker-compose.yml` + `docs/ragflow/docker-compose-base.yml` |
| 环境变量模板 | `docs/ragflow/.env.example` |
| 官方快速开始 | <https://github.com/infiniflow/ragflow/blob/v0.27.2/README.md#-start-up-the-server> |

**为什么不是 v1.0.0-rc2**：截至 2026-10-17，`v1.0.0-rc2` 仍是候选发布版，稳定性未验证；演示环境固定使用最新稳定版 `v0.27.2`。

配置快照的来源、SHA-256 与改动说明见 [`docs/ragflow/README.md`](ragflow/README.md)。两个 compose 文件与上游逐字节一致；只有 `.env.example` 做了脱敏和两处本地化调整。

## 2. 前置条件与资源处理

### 2.1 官方要求与本机实测

| 项目 | 官方要求 | 本机实测 | 状态 |
| --- | --- | --- | --- |
| CPU | ≥ 4 核 | 6 核 12 线程 | ✅ |
| 内存 | ≥ 16 GB | 15.34 GB | ⚠️ |
| 磁盘 | ≥ 50 GB 可用 | C: 16.46 GB / D: 216.8 GB | ❌（C 盘） |
| Docker | ≥ 24.0.0 | 29.7.2 | ✅ |
| Docker Compose | ≥ v2.26.1 | v5.5.0 | ✅ |
| Docker VM 内存 | 建议 ≥ 12 GB | 7.43 GB | ⚠️ |
| `vm.max_map_count` | ≥ 262144 | 262144 | ✅ |
| Web 端口 | 默认 80 | 本方案改用 8080 | ✅ 空闲 |

**结论：先处理磁盘和 Docker VM 内存，再执行第 5 节。**

### 2.2 磁盘：把 Docker 数据迁到 D 盘（必须）

RAGFlow 镜像、Elasticsearch、MySQL 和后续索引数据会占用约 20–50 GB。本机 C 盘只剩约 16 GB，D 盘有约 216 GB。

推荐操作（Docker Desktop 4.89）：

1. 退出所有容器：`docker compose stop`（如果已经启动过）。
2. 打开 Docker Desktop → **Settings → Resources → Advanced → Disk image location**。
3. 选择 `D:\Docker\DockerDesktopWSL`（目录可自建），点击 **Apply & restart**。
4. 迁移完成后确认：
   ```powershell
   docker info --format '{{.DockerRootDir}}'
   Get-PSDrive C, D | Select-Object Name, @{n='FreeGB'; e={[math]::Round($_.Free/1GB,1)}}
   ```
5. C 盘应释放出原 WSL 磁盘镜像占用的空间；确认 C 盘可用空间达到 50 GB 左右再继续。

> 如果不能迁移，也可以清理 C 盘（Windows 更新缓存、休眠文件、旧 Docker 镜像 `docker system prune -a`）直到可用空间 ≥ 50 GB。不要删除 `D:\` 上的个人数据。

### 2.3 内存：调整 WSL/Docker VM 上限（必须）

本机物理内存 15.34 GB，Docker VM 目前只有 7.43 GB，低于 RAGFlow 官方建议。新建或修改 `%UserProfile%\.wslconfig`：

```ini
[wsl2]
memory=12GB
processors=8
swap=4GB
localhostForwarding=true
```

然后：

```powershell
wsl --shutdown
# 重新启动 Docker Desktop，等待引擎就绪
docker info --format '{{.MemTotal}}'
```

`MemTotal` 应接近 12 GB。物理内存 15.34 GB 下给 WSL 12 GB 会压缩 Windows 自身余量，演示时关闭浏览器多余标签、Office 等大内存程序。

配套地，`.env.example` 已把 `MEM_LIMIT` 从 8 GB 降到 6 GB，避免 Elasticsearch 的 `mem_limit` 超过 VM 总内存。

### 2.4 `vm.max_map_count`（每次 Docker 重启后复核）

Elasticsearch 要求 `vm.max_map_count >= 262144`：

```powershell
wsl -d docker-desktop sysctl vm.max_map_count
# 若小于 262144：
wsl -d docker-desktop sysctl -w vm.max_map_count=262144
```

本机 2026-10-17 实测为 `262144`，已满足。Docker Desktop 升级或 WSL 重启后需重新检查。

### 2.5 端口占用检查

| 端口 | 用途 | 检查命令 |
| --- | --- | --- |
| 8080 | RAGFlow Web UI | `Test-NetConnection 127.0.0.1 -Port 8080` |
| 9380 | RAGFlow HTTP API | `Test-NetConnection 127.0.0.1 -Port 9380` |
| 9381 | Admin API | `Test-NetConnection 127.0.0.1 -Port 9381` |
| 1200 | Elasticsearch | `Test-NetConnection 127.0.0.1 -Port 1200` |
| 3306 | MySQL | `Test-NetConnection 127.0.0.1 -Port 3306` |
| 9000/9001 | MinIO API/Console | `Test-NetConnection 127.0.0.1 -Port 9000` |
| 6379 | Valkey | `Test-NetConnection 127.0.0.1 -Port 6379` |

若 8080 被占用，修改 `.env` 中的 `SVR_WEB_HTTP_PORT`，并同步修改本文所有访问地址。

## 3. 获取 RAGFlow v0.27.2

在 PowerShell 中执行：

```powershell
New-Item -ItemType Directory -Force C:\RAG库\deploy | Out-Null
git clone --branch v0.27.2 --depth 1 https://github.com/infiniflow/ragflow.git C:\RAG库\deploy\ragflow
Set-Location C:\RAG库\deploy\ragflow\docker
git log -1 --oneline
```

预期 commit 为 `a024bea`。确认当前目录包含 `docker-compose.yml`、`docker-compose-base.yml`、`entrypoint.sh`、`init.sql`、`service_conf.yaml.template`。

> 为什么不在 `docs/ragflow/` 里直接启动：快照缺少入口脚本和初始化 SQL。快照只用于评审与追溯，运行时使用完整克隆。

## 4. 生成本地 `.env`

### 4.1 复制模板并替换占位密码

```powershell
Copy-Item C:\RAG库\enterprise-rag-kb\docs\ragflow\.env.example .env

# 为本地演示设置统一强密码（至少 16 位，不要复用企业密码）
$password = Read-Host "输入本地演示密码"
$text = Get-Content .env -Raw
$text = $text -replace 'CHANGE_ME_[A-Z_]+', $password
[IO.File]::WriteAllText((Join-Path (Get-Location) '.env'), $text, (New-Object System.Text.UTF8Encoding($false)))

# 确认没有残留占位符
Select-String -Path .env -Pattern 'CHANGE_ME'
```

`ADMIN_DEFAULT_PASSWORD` 会一并被替换，它是首次登录管理界面 `admin@ragflow.io` 的密码，**必须记入密码管理器**。如果忘记，可在首次启动日志目录 `ragflow-logs/admin_bootstrap_password.txt` 中找到系统生成的密码（仅在未设置 `ADMIN_DEFAULT_PASSWORD` 时生成）。

### 4.2 确认关键变量

```powershell
Select-String -Path .env -Pattern '^RAGFLOW_IMAGE|^SVR_WEB_HTTP_PORT|^MEM_LIMIT|^DOC_ENGINE|^TZ'
```

应看到：

```text
RAGFLOW_IMAGE=infiniflow/ragflow:v0.27.2
SVR_WEB_HTTP_PORT=8080
MEM_LIMIT=6442450944
DOC_ENGINE=${DOC_ENGINE:-elasticsearch}
TZ=Asia/Shanghai
```

### 4.3 校验 compose 配置

不拉镜像、不启动容器，只做语法与变量校验：

```powershell
docker compose --env-file .env -f docker-compose.yml config --quiet
```

无输出即通过。也可以查看解析后的服务列表：

```powershell
docker compose --env-file .env -f docker-compose.yml config --services
```

预期包含 `es01`、`mysql`、`minio`、`redis`、`ragflow-cpu`（启用 `cpu` profile 时）。

> 校验仓库中的快照时，需要把 `.env.example` 临时复制为 `.env`（compose 的 `env_file: .env` 会被检查），校验后删除：
>
> ```powershell
> Copy-Item docs/ragflow/.env.example docs/ragflow/.env
> docker compose -f docs/ragflow/docker-compose.yml config --quiet
> Remove-Item docs/ragflow/.env
> ```
>
> 2026-10-17 已按上述命令验证通过（输出为空，退出码 0）。

## 5. 拉取镜像并启动

### 5.1 拉取镜像

```powershell
docker compose -f docker-compose.yml pull
```

镜像总量约数 GB，首次拉取取决于网络。若 Docker Hub 超时，可在 `.env` 中改用官方注释提供的镜像地址：

```dotenv
RAGFLOW_IMAGE=registry.cn-hangzhou.aliyuncs.com/infiniflow/ragflow:v0.27.2
```

Elasticsearch、MySQL 等基础镜像如无法拉取，需要配置 Docker Desktop 的 registry mirror（公司网络有代理时同时配置 HTTP/HTTPS Proxy）。

### 5.2 启动

```powershell
docker compose -f docker-compose.yml up -d
docker compose ps
```

首次启动需要初始化 MySQL、Elasticsearch 索引和 MinIO bucket，通常 2–5 分钟。查看 RAGFlow 日志：

```powershell
docker compose logs -f ragflow-cpu
```

看到类似下面的 banner 表示服务已就绪：

```text
    ____   ___    ______ ______ __
   / __ \ /   |  / ____// ____// /____  _      __
  / /_/ // /| | / / __ / /_   / // __ \| | /| / /
 / _, _// ___ |/ /_/ // __/  / // /_/ /| |/ |/ /
/_/ |_|/_/  |_|\____//_/    /_/ \____/ |__/|__/

* Running on all addresses (0.0.0.0)
```

按 `Ctrl+C` 只退出日志，不会停止容器。

### 5.3 健康检查

```powershell
docker compose ps
docker inspect --format '{{.State.Health.Status}}' docker-es01-1
```

所有服务应为 `running`，`es01` 为 `healthy`。容器名以 `docker compose ps` 实际输出为准（项目名来自 `docker` 目录）。

## 6. 首次登录

| 入口 | 地址 | 账号 |
| --- | --- | --- |
| 业务界面 | <http://localhost:8080> | 在管理界面创建的业务账号 |
| 管理界面 | <http://localhost:8080/admin> | `admin@ragflow.io` / `.env` 中的 `ADMIN_DEFAULT_PASSWORD` |

首次使用建议：

1. 用 `admin@ragflow.io` 登录 `/admin`；
2. 在 **User management** 中创建一个日常业务账号（例如 `demo@example.com`），不要长期共用超级管理员；
3. 用业务账号登录主界面；
4. 若管理界面提示密码错误，查看 `docker/ragflow-logs/admin_bootstrap_password.txt`；
5. 超级管理员密码修改功能在 v0.27.2 尚未提供，因此务必把初始密码保存在密码管理器，并限制管理界面访问。

## 7. 配置在线模型（阿里云百炼）

### 7.1 准备 API key

1. 登录阿里云百炼控制台，创建 API key；
2. 确认已开通 `qwen-plus` 与 `text-embedding-v4` 的调用权限；
3. 将 key 放入本机环境变量（不要写入仓库）：

```powershell
# 仅当前 PowerShell 会话有效
$env:DASHSCOPE_API_KEY = Read-Host "粘贴 DashScope API Key"
```

### 7.2 在 RAGFlow 中添加模型提供商

1. 业务界面右上角头像 → **User settings → Model providers**；
2. 在 **Available models** 选择 **Tongyi-Qianwen**（阿里云百炼）；
3. 新建实例，填入：
   - API Key：从环境变量读取的 `DASHSCOPE_API_KEY`
   - Base URL：保持默认（`https://dashscope.aliyuncs.com/compatible-mode/v1`）
4. 点击 **Verify connection**，通过后保存；
5. 添加模型：
   - `qwen-plus`，类型 LLM
   - `text-embedding-v4`，类型 Embedding
6. 在 **Set default models** 中把默认 LLM 设为 `qwen-plus`，默认 Embedding 设为 `text-embedding-v4`。

> 模型 key 保存在本地 MySQL 中，不进入 Git。截图、录屏和文档中不得出现完整 key；一旦疑似泄露，立即在百炼控制台吊销并重建。

### 7.3 连通性验证

在模型提供商页面点击模型测试（或新建一个临时聊天），确认：

- 对话模型能返回中文回答；
- Embedding 模型测试通过，无 401/404；
- 默认模型设置已生效。

## 8. 创建知识库并验证引用（第二步执行）

### 8.1 建库

1. 业务界面 → **Knowledge Base → Create knowledge base**；
2. 名称：`enterprise-mock-kb`；
3. Embedding 模型：`text-embedding-v4`；
4. 解析方法先选 **General**（后续可按 PDF/Word 类型调整为 Manual/Paper）；
5. 保存。

### 8.2 上传与解析

1. 上传 `data/` 下的三份虚构资料（PDF/Word）；
2. 对每个文件点击 **Parse**，等待解析完成；
3. 打开 chunk 预览，检查：
   - 标题层级是否保留；
   - 表格数值是否完整；
   - 页眉页脚是否产生噪声；
   - 切片长度是否在 300–800 字左右（按需调整）。

### 8.3 创建聊天助手

1. **Chat → Create assistant**；
2. 关联 `enterprise-mock-kb`；
3. 模型选 `qwen-plus`；
4. 系统提示词加入引用要求，例如：
   ```text
   你是企业内部资料助手。只根据检索到的资料回答；
   每个事实性结论后必须保留引用编号；
   资料中没有答案时，明确回答“资料中未找到”，不要编造。
   ```
5. 确认回答下方显示引用区域。

### 8.4 引用验收

用 `tests/` 中的问题逐条验证：

- [ ] 回答包含事实性结论时，至少出现 1 条引用；
- [ ] 点击引用能展开命中的 chunk 原文；
- [ ] 引用片段确实包含回答中的数值/结论；
- [ ] 无答案问题返回“未找到”，而不是编造；
- [ ] 跨文档问题能同时引用多份资料。

任一条不满足，记录到 `tests/results/` 并在 `known-issues.md` 登记。

## 9. 日常运维

```powershell
# 查看状态
docker compose ps

# 查看资源占用
docker stats --no-stream

# 查看日志
docker compose logs -f ragflow-cpu
docker compose logs -f es01

# 重启
docker compose restart

# 停止（保留数据卷）
docker compose stop

# 停止并删除容器/网络（保留命名卷）
docker compose down
```

> **禁止**执行 `docker compose down -v`：`-v` 会删除 Elasticsearch、MySQL、MinIO 的数据卷，知识库和已解析文档会全部丢失。

### 备份

至少备份三样：

1. `.env`（密码与端口配置）；
2. MySQL 元数据：
   ```powershell
   docker compose exec mysql sh -c 'exec mysqldump -uroot -p"$MYSQL_PASSWORD" --all-databases' > ragflow-mysql-backup.sql
   ```
3. MinIO 中的原始文件（或使用 RAGFlow 知识库导出功能）。

备份文件包含业务数据与密码，禁止提交仓库。

## 10. 故障排查

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 拉镜像超时 | Docker Hub 网络受限 | 改用 `.env` 中的阿里云/华为云镜像地址；配置代理 |
| `es01` 反复重启 / 退出码 137 | 内存不足或 `vm.max_map_count` 太小 | 提高 WSL 内存到 12 GB；执行 `sysctl -w vm.max_map_count=262144`；降低 `MEM_LIMIT` |
| RAGFlow 启动后 502/无法访问 | 服务仍在初始化 | `docker compose logs -f ragflow-cpu` 等待 banner；检查 MySQL 健康状态 |
| 8080 被占用 | 其他 Web 服务 | 改 `SVR_WEB_HTTP_PORT`；`Get-NetTCPConnection -LocalPort 8080` 定位进程 |
| MySQL 认证失败 | `.env` 密码在首次初始化后被修改 | 密码只在首次初始化时生效；不要直接改已初始化数据库的 `.env` 密码 |
| 模型验证 401 | key 错误、欠费或 Base URL 不对 | 核对 `DASHSCOPE_API_KEY`；确认 Base URL 含 `/compatible-mode/v1`；检查百炼额度 |
| 引用为空 | 未解析、未命中或引用开关关闭 | 检查 chunk 是否生成；调大 top-k；确认助手显示引用 |
| 磁盘写满 | 镜像/索引/日志增长 | `docker system df`；清理无用镜像；把数据迁到 D 盘 |
| 管理界面密码错误 | 未设置或记错 `ADMIN_DEFAULT_PASSWORD` | 查看 `ragflow-logs/admin_bootstrap_password.txt` |

更多环境问题记录在仓库根目录 [`known-issues.md`](../known-issues.md)。

## 11. 安全注意事项

1. **不要暴露基础组件端口**：compose 默认把 3306/1200/9000/6379 发布到主机。演示机不要接入不可信网络；必要时用 Windows 防火墙限制入站，或增加 override 把端口绑定到 `127.0.0.1`。
2. **不要提交 `.env`**：仓库只保留 `.env.example`。
3. **使用虚构资料**：第一步和第二步都只使用 `data/` 下的虚构文件。
4. **最小化账号**：超级管理员只用于初始化，业务操作使用普通账号。
5. **定期轮换 key**：百炼 key 泄露后立即吊销。

## 附录 A：官方 `docker-compose.yml`（v0.27.2，逐字节原样）

<details>
<summary>展开查看 docker-compose.yml 全文（166 行）</summary>

```yaml
include:
  - ./docker-compose-base.yml
# To ensure that the container processes the locally modified `service_conf.yaml.template` instead of the one included in its image, you need to mount the local `service_conf.yaml.template` to the container.
services:
  ragflow-cpu:
    depends_on:
      mysql:
        condition: service_healthy
        required: false
      nats:
        condition: service_healthy
        required: false
    profiles:
      - cpu
    image: ${RAGFLOW_IMAGE}
    ulimits:
      nofile:
        soft: 65535
        hard: 65535
      nproc:
        soft: 65535
        hard: 65535
    # Example configuration to set up an MCP server:
    # command:
    #   - --enable-mcpserver
    #   - --mcp-host=0.0.0.0
    #   - --mcp-port=9382
    #   - --mcp-base-url=http://127.0.0.1:9380
    #   - --mcp-script-path=/ragflow/mcp/server/server.py
    #   - --mcp-mode=self-host
    #   - --mcp-host-api-key=ragflow-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Optional transport flags for MCP (customize if needed).
    # Host mode need to combined with --no-transport-streamable-http-enabled flag, namely, host+streamable-http is not supported yet.
    # The following are enabled by default unless explicitly disabled with --no-<flag>.
    #   - --no-transport-sse-enabled # Disable legacy SSE endpoints (/sse and /messages/)
    #   - --no-transport-streamable-http-enabled #  Disable Streamable HTTP transport (/mcp endpoint)
    #   - --no-json-response # Disable JSON response mode in Streamable HTTP transport (instead of SSE over HTTP)

    # Example configuration to start Admin server:
    command:
      - --enable-adminserver
      - --init-model-provider-tables
    ports:
      - ${SVR_WEB_HTTP_PORT}:80
      - ${SVR_WEB_HTTPS_PORT}:443
      - ${SVR_HTTP_PORT}:9380
      - ${ADMIN_SVR_HTTP_PORT}:9381
      - ${SVR_MCP_PORT}:9382 # entry for MCP (host_port:docker_port). The docker_port must match the value you set for `mcp-port` above.
      - ${GO_HTTP_PORT}:9384
      - ${GO_ADMIN_PORT}:9383
    environment:
      # Shared secret used to authenticate towards sandbox-executor-manager.
      # Must match SANDBOX_EXECUTOR_MANAGER_API_TOKEN on that service.
      - SANDBOX_EXECUTOR_MANAGER_API_TOKEN=${SANDBOX_EXECUTOR_MANAGER_API_TOKEN:-}
    volumes:
      - ./ragflow-logs:/ragflow/logs
      # - ./nginx/ragflow.conf:/etc/nginx/conf.d/ragflow.conf
      # - ./nginx/proxy.conf:/etc/nginx/proxy.conf
      # - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./service_conf.yaml.template:/ragflow/conf/service_conf.yaml.template
      - ./entrypoint.sh:/ragflow/entrypoint.sh
    env_file: .env
    networks:
      - ragflow
    restart: unless-stopped
    # https://docs.docker.com/engine/daemon/prometheus/#create-a-prometheus-configuration
    # If you use Docker Desktop, the --add-host flag is optional. This flag ensures that the host's internal IP is exposed to the Prometheus container.
    extra_hosts:
      - "host.docker.internal:host-gateway"

  ragflow-gpu:
    depends_on:
      mysql:
        condition: service_healthy
        required: false
      nats:
        condition: service_healthy
        required: false
    profiles:
      - gpu
    image: ${RAGFLOW_IMAGE}
    ulimits:
      nofile:
        soft: 65535
        hard: 65535
      nproc:
        soft: 65535
        hard: 65535
    # Example configuration to set up an MCP server:
    # command:
    #   - --enable-mcpserver
    #   - --mcp-host=0.0.0.0
    #   - --mcp-port=9382
    #   - --mcp-base-url=http://127.0.0.1:9380
    #   - --mcp-script-path=/ragflow/mcp/server/server.py
    #   - --mcp-mode=self-host
    #   - --mcp-host-api-key=ragflow-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Optional transport flags for MCP (customize if needed).
    # Host mode need to combined with --no-transport-streamable-http-enabled flag, namely, host+streamable-http is not supported yet.
    # The following are enabled by default unless explicitly disabled with --no-<flag>.
    #   - --no-transport-sse-enabled # Disable legacy SSE endpoints (/sse and /messages/)
    #   - --no-transport-streamable-http-enabled #  Disable Streamable HTTP transport (/mcp endpoint)
    #   - --no-json-response # Disable JSON response mode in Streamable HTTP transport (instead of SSE over HTTP)

    # Example configuration to start Admin server:
    command:
      - --enable-adminserver
    ports:
      - ${SVR_WEB_HTTP_PORT}:80
      - ${SVR_WEB_HTTPS_PORT}:443
      - ${SVR_HTTP_PORT}:9380
      - ${ADMIN_SVR_HTTP_PORT}:9381
      - ${SVR_MCP_PORT}:9382 # entry for MCP (host_port:docker_port). The docker_port must match the value you set for `mcp-port` above.
    volumes:
      - ./ragflow-logs:/ragflow/logs
      # - ./nginx/ragflow.conf:/etc/nginx/conf.d/ragflow.conf
      # - ./nginx/proxy.conf:/etc/nginx/proxy.conf
      # - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./service_conf.yaml.template:/ragflow/conf/service_conf.yaml.template
      - ./entrypoint.sh:/ragflow/entrypoint.sh
    environment:
      # Shared secret used to authenticate towards sandbox-executor-manager.
      # Must match SANDBOX_EXECUTOR_MANAGER_API_TOKEN on that service.
      - SANDBOX_EXECUTOR_MANAGER_API_TOKEN=${SANDBOX_EXECUTOR_MANAGER_API_TOKEN:-}
    env_file: .env
    networks:
      - ragflow
    restart: unless-stopped
    # https://docs.docker.com/engine/daemon/prometheus/#create-a-prometheus-scrape-configuration
    # If you use Docker Desktop, the --add-host flag is optional. This flag ensures that the host's internal IP is exposed to the Prometheus container.
    extra_hosts:
      - "host.docker.internal:host-gateway"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]


  # executor:
  #   depends_on:
  #     mysql:
  #       condition: service_healthy
  #   image: ${RAGFLOW_IMAGE}
  #   volumes:
  #     - ./ragflow-logs:/ragflow/logs
  #     - ./nginx/ragflow.conf:/etc/nginx/conf.d/ragflow.conf
  #   env_file: .env
  #   entrypoint: "/ragflow/entrypoint_task_executor.sh 1 3"
  #   networks:
  #     - ragflow
  #   restart: unless-stopped
  #   # https://docs.docker.com/engine/daemon/prometheus/#create-a-prometheus-configuration
  #   # If you're using Docker Desktop, the --add-host flag is optional. This flag makes sure that the host's internal IP gets exposed to the Prometheus container.
  #   extra_hosts:
  #     - "host.docker.internal:host-gateway"
  #   deploy:
  #     resources:
  #       reservations:
  #         devices:
  #           - driver: nvidia
  #             count: all
  #             capabilities: [gpu]
```

</details>

## 附录 B：官方 `docker-compose-base.yml`（v0.27.2，逐字节原样）

<details>
<summary>展开查看 docker-compose-base.yml 全文（440 行）</summary>

```yaml
services:
  es01:
    profiles:
      - elasticsearch
    image: elasticsearch:${STACK_VERSION}
    volumes:
      - esdata01:/usr/share/elasticsearch/data
    # Official ES image ACL on /tmp denies writes for user elasticsearch (r-x only).
    # entrypoint.sh needs a writable temp dir for bash here-documents.
    tmpfs:
      - /tmp:mode=1777,size=512m
    ports:
      - ${ES_PORT}:9200
    env_file: .env
    environment:
      - node.name=es01
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
      - bootstrap.memory_lock=false
      - discovery.type=single-node
      - xpack.security.enabled=true
      - xpack.security.http.ssl.enabled=false
      - xpack.security.transport.ssl.enabled=false
      - cluster.routing.allocation.disk.watermark.low=5gb
      - cluster.routing.allocation.disk.watermark.high=3gb
      - cluster.routing.allocation.disk.watermark.flood_stage=2gb
    mem_limit: ${MEM_LIMIT}
    ulimits:
      memlock:
        soft: -1
        hard: -1
    healthcheck:
      test: ["CMD-SHELL", "curl http://localhost:9200"]
      interval: 10s
      timeout: 10s
      retries: 120
    networks:
      - ragflow
    restart: unless-stopped

  opensearch01:
    profiles:
      - opensearch
    image: opensearchproject/opensearch:2.19.1
    volumes:
      - osdata01:/usr/share/opensearch/data
    ports:
      - ${OS_PORT}:9201
    env_file: .env
    environment:
      - node.name=opensearch01
      - OPENSEARCH_PASSWORD=${OPENSEARCH_PASSWORD}
      - OPENSEARCH_INITIAL_ADMIN_PASSWORD=${OPENSEARCH_PASSWORD}
      - bootstrap.memory_lock=false
      - discovery.type=single-node
      - plugins.security.disabled=false
      - plugins.security.ssl.http.enabled=false
      - plugins.security.ssl.transport.enabled=true
      - cluster.routing.allocation.disk.watermark.low=5gb
      - cluster.routing.allocation.disk.watermark.high=3gb
      - cluster.routing.allocation.disk.watermark.flood_stage=2gb
      - http.port=9201
    mem_limit: ${MEM_LIMIT}
    ulimits:
      memlock:
        soft: -1
        hard: -1
    healthcheck:
      test: ["CMD-SHELL", "curl http://localhost:9201"]
      interval: 10s
      timeout: 10s
      retries: 120
    networks:
      - ragflow
    restart: unless-stopped

  infinity:
    profiles:
      - infinity
    image: infiniflow/infinity:v0.7.3-x64-v3
    volumes:
      - infinity_data:/var/infinity
      - ./infinity_conf.toml:/infinity_conf.toml
    command: ["-f", "/infinity_conf.toml"]
    ports:
      - ${INFINITY_THRIFT_PORT}:23817
      - ${INFINITY_HTTP_PORT}:23820
      - ${INFINITY_PSQL_PORT}:5432
    env_file: .env
    mem_limit: ${MEM_LIMIT}
    ulimits:
      nofile:
        soft: 500000
        hard: 500000
    networks:
      - ragflow
    healthcheck:
      test: ["CMD", "curl", "http://localhost:23820/admin/node/current"]
      interval: 10s
      timeout: 10s
      retries: 120
    restart: unless-stopped

  serenedb:
    profiles:
      - serenedb
    image: serenedb/serenedb:26.07.5
    env_file: .env
    environment:
      - POSTGRES_PASSWORD=${SERENEDB_PASSWORD}
    ports:
      - ${SERENEDB_PORT}:7890
    volumes:
      - serenedb_data:/var/lib/serenedb
    mem_limit: ${MEM_LIMIT}
    networks:
      - ragflow
    healthcheck:
      test: ["CMD", "pg_isready", "-h", "127.0.0.1", "-p", "7890", "-U", "postgres"]
      interval: 10s
      timeout: 10s
      retries: 120
    restart: unless-stopped

  oceanbase:
    profiles:
      - oceanbase
    image: oceanbase/oceanbase-ce:4.4.1.0-100000032025101610
    entrypoint: ["bash", "/root/boot/ragflow-oceanbase-entrypoint.sh"]
    ulimits:
      nofile:
        soft: 655350
        hard: 655350
    volumes:
      - ./oceanbase/data:/root/ob
      - ./oceanbase/conf:/root/.obd/cluster
      - ./oceanbase/init.d:/root/boot/init.d
      - ./oceanbase-entrypoint.sh:/root/boot/ragflow-oceanbase-entrypoint.sh:ro
    ports:
      - ${OCEANBASE_PORT:-2881}:2881
    env_file: .env
    environment:
      - MODE=normal
      - OB_SERVER_IP=127.0.0.1
    mem_limit: ${MEM_LIMIT}
    healthcheck:
      test: [ 'CMD-SHELL', 'obclient -h127.0.0.1 -P2881 -uroot@${OB_TENANT_NAME:-ragflow} -p${OB_TENANT_PASSWORD:-infini_rag_flow} -e "CREATE DATABASE IF NOT EXISTS ${OCEANBASE_DOC_DBNAME:-ragflow_doc};"' ]
      interval: 10s
      retries: 30
      start_period: 30s
      timeout: 10s
    networks:
      - ragflow
    restart: unless-stopped

  seekdb:
    profiles:
      - seekdb
    image: oceanbase/seekdb:latest
    container_name: seekdb
    volumes:
      - ./seekdb:/var/lib/oceanbase
    ports:
      - ${SEEKDB_PORT:-2881}:2881
    env_file: .env
    environment:
      - ROOT_PASSWORD=${SEEKDB_PASSWORD:-infini_rag_flow}
      - MEMORY_LIMIT=${SEEKDB_MEMORY_LIMIT:-2G}
      - REPORTER=ragflow-seekdb
    mem_limit: ${MEM_LIMIT}
    healthcheck:
      test: ['CMD-SHELL', 'mysql -h127.0.0.1 -P2881 -uroot -p${SEEKDB_PASSWORD:-infini_rag_flow} -e "CREATE DATABASE IF NOT EXISTS ${SEEKDB_DOC_DBNAME:-ragflow_doc};"']
      interval: 5s
      retries: 60
      timeout: 5s
    networks:
      - ragflow
    restart: unless-stopped

  sandbox-executor-manager:
    profiles:
      - sandbox
    image: ${SANDBOX_EXECUTOR_MANAGER_IMAGE-infiniflow/sandbox-executor-manager:latest}
    privileged: true
    # Bind to loopback only: the /run endpoint executes arbitrary sandboxed
    # code. RAGFlow reaches this service over the shared `ragflow` network.
    ports:
      - 127.0.0.1:${SANDBOX_EXECUTOR_MANAGER_PORT:-9385}:9385
    env_file: .env
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - ragflow
    security_opt:
      - no-new-privileges:true
    environment:
      - SANDBOX_EXECUTOR_MANAGER_POOL_SIZE=${SANDBOX_EXECUTOR_MANAGER_POOL_SIZE:-3}
      - SANDBOX_BASE_PYTHON_IMAGE=${SANDBOX_BASE_PYTHON_IMAGE:-infiniflow/sandbox-base-python:latest}
      - SANDBOX_BASE_NODEJS_IMAGE=${SANDBOX_BASE_NODEJS_IMAGE:-infiniflow/sandbox-base-nodejs:latest}
      - SANDBOX_ENABLE_SECCOMP=${SANDBOX_ENABLE_SECCOMP:-false}
      - SANDBOX_MAX_MEMORY=${SANDBOX_MAX_MEMORY:-256m}
      - SANDBOX_TIMEOUT=${SANDBOX_TIMEOUT:-10s}
      # Shared secret for the /run API. Set it in .env (same value is passed
      # to the ragflow service); when empty the API stays open (backwards
      # compatible) but a warning is logged.
      - SANDBOX_EXECUTOR_MANAGER_API_TOKEN=${SANDBOX_EXECUTOR_MANAGER_API_TOKEN:-}
      # Sandbox runner containers get no external network by default.
      - SANDBOX_CONTAINER_NETWORK=${SANDBOX_CONTAINER_NETWORK:-none}
    healthcheck:
      test: ["CMD", "curl", "http://localhost:9385/healthz"]
      interval: 10s
      timeout: 10s
      retries: 120
    restart: unless-stopped

  mysql:
    profiles:
      - mysql
      - metadata-mysql
      - metadata-MySQL
      - metadata-MYSQL
    # mysql:5.7 linux/arm64 image is unavailable.
    image: mysql:8.0.40
    env_file: .env
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_PASSWORD}
    command:
      --max_connections=1000
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci
      --default-authentication-plugin=mysql_native_password
      --tls_version="TLSv1.2,TLSv1.3"
      --init-file /data/application/init.sql
      --binlog_expire_logs_seconds=604800
    ports:
      - ${EXPOSE_MYSQL_PORT}:3306
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/data/application/init.sql
    networks:
      - ragflow
    healthcheck:
      test: ["CMD", "mysqladmin" ,"ping", "-uroot", "-p${MYSQL_PASSWORD}"]
      interval: 10s
      timeout: 10s
      retries: 120
    restart: unless-stopped

  minio:
    image: pgsty/silo:RELEASE.2026-08-06T00-00-00Z
    command: ["server", "--console-address", ":9001", "/data"]
    ports:
      - ${MINIO_PORT}:9000
      - ${MINIO_CONSOLE_PORT}:9001
    env_file: .env
    environment:
      - MINIO_ROOT_USER=${MINIO_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_PASSWORD}
    volumes:
      - minio_data:/data
    networks:
      - ragflow
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 10s
      retries: 120

  redis:
    # swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/valkey/valkey:8
    image: valkey/valkey:8
    command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}", "--maxmemory", "128mb", "--maxmemory-policy", "volatile-lru"]
    env_file: .env
    ports:
      - ${REDIS_PORT}:6379
    volumes:
      - redis_data:/data
    networks:
      - ragflow
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 10s
      retries: 120

  jaeger:
    profiles:
      - jaeger
    image: jaegertracing/jaeger:${JAEGER_VERSION:-2.19.0}
    ports:
      - ${JAEGER_OTLP_GRPC_PORT:-4317}:4317
      - ${JAEGER_OTLP_HTTP_PORT:-4318}:4318
      - ${JAEGER_UI_PORT:-16686}:16686
    env_file: .env
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - ragflow
    restart: unless-stopped

  nats:
    profiles:
      - ragflow-go
    image: nats:2.14.2
    ports:
      - ${EXPOSE_NATS_PORT:-4222}:4222
      - "8222:8222"
    volumes:
      - nats_data:/data
    command: -js -sd /data
    env_file: .env
    networks:
      - ragflow
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "nats-server", "--health-check"]
      interval: 10s
      timeout: 10s
      retries: 30

  tei-cpu:
    profiles:
      - tei-cpu
    image: ${TEI_IMAGE_CPU}
    hostname: tei
    ports:
      - ${TEI_PORT-6380}:80
    env_file: .env
    networks:
      - ragflow
    command: ["--model-id", "/data/${TEI_MODEL}", "--auto-truncate"]
    restart: unless-stopped


  tei-gpu:
    profiles:
      - tei-gpu
    image: ${TEI_IMAGE_GPU}
    hostname: tei
    ports:
      - ${TEI_PORT-6380}:80
    env_file: .env
    networks:
      - ragflow
    command: ["--model-id", "/data/${TEI_MODEL}", "--auto-truncate"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped


  kibana:
    profiles:
      - kibana
    image: kibana:${STACK_VERSION}
    ports:
      - ${KIBANA_PORT-5601}:5601
    env_file: .env
    volumes:
      - kibana_data:/usr/share/kibana/data
    depends_on:
      es01:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5601/api/status"]
      interval: 10s
      timeout: 10s
      retries: 120
    networks:
      - ragflow
    restart: unless-stopped


  clickhouse:
    profiles:
      - clickhouse
    image: clickhouse/clickhouse-server:26.5.5.8
    volumes:
      - clickhouse_data:/var/lib/clickhouse
      - ./init-clickhouse.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - ${EXPOSE_CLICKHOUSE_TCP_PORT:-9900}:9000
      - ${CLICKHOUSE_HTTP_PORT:-8123}:8123
    env_file: .env
    environment:
      - CLICKHOUSE_USER=${CLICKHOUSE_USER:-ragflow}
      - CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD:-infini_rag_flow}
      - CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1
    mem_limit: ${MEM_LIMIT}
    ulimits:
      nofile:
        soft: 655350
        hard: 655350
    healthcheck:
      test: ["CMD", "clickhouse-client", "--user", "${CLICKHOUSE_USER:-ragflow}", "--password", "${CLICKHOUSE_PASSWORD:-infini_rag_flow}", "-q", "SELECT 1"]
      interval: 10s
      timeout: 10s
      retries: 30
      start_period: 30s
    networks:
      - ragflow
    restart: unless-stopped


volumes:
  esdata01:
    driver: local
  osdata01:
    driver: local
  infinity_data:
    driver: local
  serenedb_data:
    driver: local
  ob_data:
    driver: local
  seekdb_data:
    driver: local
  mysql_data:
    driver: local
  minio_data:
    driver: local
  redis_data:
    driver: local
  tei_data:
    driver: local
  kibana_data:
    driver: local
  nats_data:
    driver: local
  clickhouse_data:
    driver: local

networks:
  ragflow:
    driver: bridge
```

</details>

## 附录 C：核心环境变量

| 变量 | 本地方案值 | 说明 |
| --- | --- | --- |
| `RAGFLOW_IMAGE` | `infiniflow/ragflow:v0.27.2` | 固定稳定版 |
| `SVR_WEB_HTTP_PORT` | `8080` | Web UI 端口 |
| `SVR_HTTP_PORT` | `9380` | 后端 API 端口 |
| `DOC_ENGINE` | `elasticsearch` | 文档引擎，使用 compose 集成的 ES |
| `MEM_LIMIT` | `6442450944` | ES 等容器内存上限（6 GiB） |
| `ELASTIC_PASSWORD` | `CHANGE_ME_*` | 本地部署时替换为强密码 |
| `MYSQL_PASSWORD` | `CHANGE_ME_*` | MySQL root 密码 |
| `MINIO_PASSWORD` | `CHANGE_ME_*` | MinIO 密码 |
| `REDIS_PASSWORD` | `CHANGE_ME_*` | Valkey 密码 |
| `ADMIN_DEFAULT_PASSWORD` | `CHANGE_ME_*` | `admin@ragflow.io` 初始密码 |
| `TZ` | `Asia/Shanghai` | 时区 |
| `COMPOSE_PROFILES` | 由 `DOC_ENGINE`/`DEVICE` 推导 | 默认启用 elasticsearch + cpu + mysql |

模型 API key 不写入 `.env`，也不写入仓库；由部署人在 RAGFlow 界面配置，值来源于本机环境变量 `DASHSCOPE_API_KEY`。
