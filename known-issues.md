# 已知问题清单

> 更新时间：2026-10-17
> 适用阶段：第一步（项目初始化与环境准备）
> 状态说明：`待处理` / `已规避` / `已解决` / `已知限制`

## 汇总

| ID | 级别 | 问题 | 状态 | 影响阶段 |
| --- | --- | --- | --- | --- |
| KI-001 | P1 | C 盘可用空间 16.46 GB，低于 RAGFlow 要求的 50 GB | 待处理 | 第二步启动前 |
| KI-002 | P1 | Docker VM 内存 7.43 GB，低于演示建议的 12 GB | 待处理 | 第二步启动前 |
| KI-003 | P3 | Docker Desktop 未开机自启，检查时引擎未运行 | 已规避 | 每次演示 |
| KI-004 | P2 | 物理内存 15.34 GB，略低于官方建议 16 GB | 已知限制 | 第二步及演示 |
| KI-005 | P2 | 百炼 API key 尚未配置，模型连通性未验证 | 待处理 | 第二步 |
| KI-006 | P3 | skill-atlas 拉取大数据包时出现 IncompleteRead | 已规避 | 工具使用 |
| KI-007 | P2 | compose 默认把 MySQL/ES/MinIO/Valkey 端口发布到主机 | 待处理 | 第二步安全加固 |
| KI-008 | P3 | RAGFlow v0.27.2 管理界面暂不支持修改超级管理员密码 | 已知限制 | 第二步 |
| KI-009 | P3 | 尚未端到端启动验证，仅通过 compose 语法校验 | 已知限制 | 第二步 |

---

## KI-001：C 盘空间不足

- **级别**：P1（阻塞部署）
- **状态**：待处理
- **现象**：2026-10-17 实测 C 盘可用 16.46 GB；RAGFlow 官方要求磁盘 ≥ 50 GB；D 盘可用 216.8 GB。
- **证据**：
  - `scripts/check-env.ps1` 输出：`Free space on C: | 16.46 GB | >= 50 GB | FAIL`
  - 官方要求：<https://github.com/infiniflow/ragflow/blob/v0.27.2/README.md#-prerequisites>
- **影响**：RAGFlow 镜像、Elasticsearch、MySQL、索引与日志可能写满 C 盘，导致容器启动失败或数据损坏。
- **规避方案**：
  1. 将 Docker Desktop 磁盘镜像迁到 `D:\Docker\DockerDesktopWSL`（Settings → Resources → Advanced → Disk image location）；
  2. 迁移前先 `docker compose stop`，迁移后重启并确认 C 盘释放；
  3. 或清理 C 盘至 ≥ 50 GB（`docker system prune -a`、Windows 更新缓存等）。
- **后续动作**：第二步启动前复跑 `scripts/check-env.ps1`，确认 C 盘 ≥ 50 GB。
- **详细步骤**：见 `docs/deployment.md` 第 2.2 节。

## KI-002：Docker VM 内存不足

- **级别**：P1（高概率导致 Elasticsearch OOM）
- **状态**：待处理
- **现象**：Docker VM 实测 12 CPU / 7.43 GB 内存；`.env` 官方 `MEM_LIMIT` 为 8 GB，超过 VM 总内存。
- **证据**：`docker info` 显示 `MemTotal≈7.43 GB`；`scripts/check-env.ps1` 判定 FAIL。
- **影响**：Elasticsearch 或 RAGFlow 容器可能被 OOM Killer 终止（退出码 137），表现为启动后反复重启。
- **规避方案**：
  1. 在 `%UserProfile%\.wslconfig` 设置 `memory=12GB`、`processors=8`、`swap=4GB`；
  2. `wsl --shutdown` 后重启 Docker Desktop，确认 `docker info` 的 `MemTotal` 接近 12 GB；
  3. 已把 `.env.example` 的 `MEM_LIMIT` 降到 6 GiB，避免单容器上限超过 VM 内存；
  4. 演示时关闭大内存应用。
- **后续动作**：第二步启动后观察 `docker stats` 与 `docker inspect ... .State.OOMKilled`。
- **详细步骤**：见 `docs/deployment.md` 第 2.3 节。

## KI-003：Docker Desktop 引擎未运行

- **级别**：P3
- **状态**：已规避
- **现象**：环境检查开始时 `docker info` 报 `npipe:////./pipe/dockerDesktopLinuxEngine` 不存在；Docker Desktop 进程未启动。
- **证据**：启动 `Docker Desktop.exe` 后约 15 秒引擎就绪，`docker info` 返回 29.7.2。
- **影响**：未启动引擎时所有 compose 命令失败。
- **规避方案**：演示前先启动 Docker Desktop，等待托盘图标稳定；或运行 `scripts/check-env.ps1` 确认 `Docker engine` 为 PASS。
- **后续动作**：如需开机自启，在 Docker Desktop → Settings → General 中勾选 “Start Docker Desktop when you sign in”。

## KI-004：物理内存略低于官方建议

- **级别**：P2
- **状态**：已知限制
- **现象**：物理内存 15.34 GB，官方建议 ≥ 16 GB。
- **影响**：把 12 GB 分配给 WSL 后，Windows 只剩约 3.3 GB；同时打开大量浏览器标签/Office 时可能卡顿，但不阻止演示。
- **规避方案**：演示机专用于 RAGFlow；关闭不必要的应用；把 WSL 内存设为 10–12 GB 并在启动后观察。
- **后续动作**：若频繁 OOM，考虑升级内存或迁移到更高配置机器；第一版不采购云服务器。

## KI-005：在线模型 key 尚未配置

- **级别**：P2
- **状态**：待处理
- **现象**：仓库只有 `DASHSCOPE_API_KEY` 的占位约定，未配置真实 key；百炼账号额度与模型权限未验证。
- **影响**：RAGFlow 启动后无法完成对话/Embedding 调用，知识库不能解析和问答。
- **规避方案**：
  1. 在百炼控制台创建 key，确认 `qwen-plus`、`text-embedding-v4` 可用；
  2. 只通过本机环境变量/密码管理器提供，不写入仓库；
  3. 在 RAGFlow **Model providers** 中配置并验证连接。
- **后续动作**：第二步完成配置后，把本问题标记为“已解决”，并记录所用模型与额度。
- **安全要求**：任何截图、日志、文档中不得出现完整 key；泄露后立即吊销。

## KI-006：skill-atlas 拉取数据出现 IncompleteRead

- **级别**：P3（仅影响辅助工具，不影响项目）
- **状态**：已规避
- **现象**：`skill-atlas fetch/enrich` 请求 GitHub 搜索大响应时抛出 `http.client.IncompleteRead`，导致 `update` 中断；离线 demo 与 `slots` 命令正常。
- **证据**：`C:\RAG库\_tools\skill-atlas-update.log` 中的 traceback。
- **影响**：无法一次性生成全量能力位索引；不影响 RAGFlow 选型与部署。
- **规避方案**：在本地工具副本 `api.py` 的重试异常中加入 `http.client.HTTPException`，并分多次 `enrich` 断点续跑；仅修改本机 `_tools` 副本，不改上游仓库。
- **后续动作**：如后续仍需完整索引，改用稳定网络或给工具提交上游 issue。

## KI-007：基础组件端口默认暴露到主机

- **级别**：P2（安全）
- **状态**：待处理
- **现象**：官方 compose 将 Elasticsearch 1200、MySQL 3306、MinIO 9000/9001、Valkey 6379 发布到主机所有网卡。
- **影响**：同一局域网内的其他机器可能访问数据库/对象存储；默认密码若未改风险更高。
- **规避方案**：
  1. 已强制 `.env.example` 使用 `CHANGE_ME_*`，部署时必须替换；
  2. 演示机不接入不可信网络；
  3. 用 Windows 防火墙限制入站，或在 `docker-compose.override.yml` 中把基础组件端口绑定到 `127.0.0.1`；
  4. 不把 8080 以外的端口映射到公网。
- **后续动作**：第二步启动后执行 `Get-NetTCPConnection -State Listen` 核对监听地址，并补防火墙规则。

## KI-008：管理界面暂不支持修改超级管理员密码

- **级别**：P3
- **状态**：已知限制
- **现象**：RAGFlow v0.27.2 官方文档明确 “Change the Admin Account Password: This feature is not available yet”。
- **来源**：<https://github.com/infiniflow/ragflow/blob/v0.27.2/docs/administrator/admin/admin_ui/before_you_begin.md>
- **影响**：`admin@ragflow.io` 的初始密码无法在界面修改；若泄露，管理界面有风险。
- **规避方案**：
  1. 初始密码使用随机强密码并存密码管理器；
  2. 日常业务使用单独创建的普通账号；
  3. 管理界面仅本机访问，不暴露公网；
  4. 如需轮换，按官方 Admin CLI 或后续版本文档处理。
- **后续动作**：升级 RAGFlow 时复查该功能是否已提供。

## KI-009：尚未端到端启动验证

- **级别**：P3
- **状态**：已知限制（第一步范围）
- **现象**：第一步只完成环境检查、配置拉取与文档；未执行 `docker compose pull/up`，未验证登录、模型调用、文档入库与引用。
- **证据**：仅执行 `docker compose config --quiet` 校验，退出码 0。
- **影响**：部署步骤与资源调整尚未在真实容器中跑通，第二步可能出现未预见的问题。
- **规避方案**：第二步严格按 `docs/deployment.md` 执行，先处理 KI-001/KI-002，再逐项记录实际结果；失败项回填本文件。
- **后续动作**：第二步完成后补充“实际启动验证”记录与截图（不含密钥）。
