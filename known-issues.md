# 已知问题清单

> 更新时间：2026-10-18
> 适用阶段：交接复核（第二步尚未开始）
> 复核机器：Windows 10 Pro 22H2 / Intel Core i7-3770 4C8T / 15.96 GB / C 盘可用 79.31 GB
> 状态说明：`待处理` / `已规避` / `已解决` / `已知限制`
> 历史说明：KI-001、KI-002、KI-004 保留 2026-10-17 旧机基线；新机结论单列，不删除旧证据。

## 汇总

| ID | 级别 | 问题 | 新机复核（2026-10-18） | 状态 | 影响阶段 |
| --- | --- | --- | --- | --- | --- |
| KI-001 | P1 | C 盘可用空间低于 RAGFlow 要求的 50 GB | C 盘 79.31 GB，已达标 | 已解决 | 第二步启动前 |
| KI-002 | P1 | Docker VM 内存低于演示建议的 12 GB | 仍存在（未验证）：Docker 未安装，VM 无法实测 | 待处理 | 第二步启动前 |
| KI-003 | P3 | Docker Desktop 未开机自启 | 不适用（Docker 未安装）；安装后复核 | 已规避 | 每次演示 |
| KI-004 | P2 | 物理内存略低于官方建议 16 GB | 仍存在：15.96 GB，差 0.04 GB | 已知限制 | 第二步及演示 |
| KI-005 | P2 | 百炼 API key 尚未配置，模型连通性未验证 | 仍未配置、未验证 | 待处理 | 第二步 |
| KI-006 | P3 | skill-atlas 拉取大数据包时出现 IncompleteRead | 未复核；不影响 RAGFlow | 已规避 | 工具使用 |
| KI-007 | P2 | compose 默认把 MySQL/ES/MinIO/Valkey 端口发布到主机 | 容器未启动，待启动后复核监听地址 | 待处理 | 第二步安全加固 |
| KI-008 | P3 | RAGFlow v0.27.2 管理界面暂不支持修改超级管理员密码 | 仍适用 | 已知限制 | 第二步 |
| KI-009 | P3 | 尚未端到端启动验证，仅通过 compose 语法校验 | 仍适用；新机环境尚不具备启动条件 | 已知限制 | 第二步 |
| KI-010 | P1 | 新机未安装 Docker Desktop，WSL2/虚拟机平台未启用 | 新发现，直接阻塞第二步 | 待处理 | 第二步启动前 |
| KI-011 | P2 | Windows 10 22H2 已过常规支持期，Docker 支持状态待确认 | 新发现，安装前需决策 | 待处理 | 安装/演示前 |

---

## KI-001：C 盘空间不足

- **级别**：P1（旧机阻塞部署）
- **状态**：**已解决（新机）**
- **旧机基线（2026-10-17）**：
  - 现象：C 盘可用 16.46 GB；D 盘可用 216.8 GB。
  - 证据：`scripts/check-env.ps1` 输出 `Free space on C: | 16.46 GB | >= 50 GB | FAIL`。
  - 结论：当时未解决，需迁移 Docker 数据或清理 C 盘。
- **新机复核（2026-10-18）**：
  - C 盘：150 GB 总容量，可用 **79.31 GB**。
  - D 盘：326.93 GB 总容量，可用 320.75 GB。
  - 证据：`scripts/check-env.ps1 -Drive C` 输出 `Free space on C: | 79.31 GB | >= 50 GB | PASS`。
- **结论**：新机 C 盘已达到 ≥ 50 GB 要求，**KI-001 已解决**，无需先迁移 Docker 数据。
- **后续动作**：
  1. Docker Desktop、WSL 虚拟磁盘和镜像仍会占用 C 盘，安装并拉取镜像后需复跑脚本，保持 ≥ 50 GB；
  2. 若后续索引增长较快，可把 Docker 数据目录或 WSL 数据盘迁到 D 盘；
  3. 不在演示机上保存无关的大文件。
- **详细步骤**：见 `docs/deployment.md` 第 2.2 节。

## KI-002：Docker VM 内存不足

- **级别**：P1（高概率导致 Elasticsearch OOM）
- **状态**：**待处理（新机仍存在，尚未复测）**
- **旧机基线（2026-10-17）**：
  - 现象：Docker VM 实测 12 CPU / 7.43 GB 内存；`.env` 官方 `MEM_LIMIT` 为 8 GB，超过 VM 总内存。
  - 证据：`docker info` 显示 `MemTotal≈7.43 GB`；脚本判定 FAIL。
- **新机复核（2026-10-18）**：
  - Docker Desktop 未安装，WSL2 未启用，因此**不存在 Docker VM，无法测量 `MemTotal`**。
  - 物理内存 15.96 GB；WSL2 默认内存上限通常为 8 GB，仍低于演示建议的 12 GB。
  - 证据：`docker info` 不可达；WSL、VirtualMachinePlatform、Hyper-V 功能均为 `Disabled`。
- **结论**：旧问题**仍存在（未验证）**，不能因物理内存略增就标记为已解决。
- **规避方案**：
  1. 安装 Docker Desktop 后，在 `%UserProfile%\.wslconfig` 设置 `memory=12GB`、`processors=6`、`swap=4GB`；
  2. `wsl --shutdown` 后重启 Docker Desktop，确认 `docker info` 的 `MemTotal` 接近 12 GB；
  3. 保持 `.env.example` 的 `MEM_LIMIT=6442450944`（6 GiB），避免单容器上限超过 VM 内存；
  4. 演示时关闭大内存应用。
- **后续动作**：安装完成后先复测 VM 内存，再拉取镜像；启动后观察 `docker stats` 与 `.State.OOMKilled`。
- **详细步骤**：见 `docs/deployment.md` 第 2.3 节。

## KI-003：Docker Desktop 引擎未运行

- **级别**：P3
- **状态**：已规避
- **旧机现象（2026-10-17）**：环境检查开始时 `docker info` 报 `npipe:////./pipe/dockerDesktopLinuxEngine` 不存在；启动 `Docker Desktop.exe` 后约 15 秒引擎就绪。
- **新机复核（2026-10-18）**：Docker Desktop 未安装，本项暂不适用。
- **影响**：未启动引擎时所有 compose 命令失败。
- **规避方案**：安装后演示前先启动 Docker Desktop，等待托盘图标稳定；运行 `scripts/check-env.ps1` 确认 Docker engine 为 PASS。可在 Settings → General 勾选开机自启。

## KI-004：物理内存略低于官方建议

- **级别**：P2
- **状态**：**已知限制（新机仍存在）**
- **旧机基线（2026-10-17）**：物理内存 15.34 GB，低于官方建议 16 GB。
- **新机复核（2026-10-18）**：物理内存 **15.96 GB**（17,134,211,072 字节），仍比 16 GB 少约 0.04 GB；脚本判定 WARN。
- **影响**：把 12 GB 分配给 WSL 后，Windows 只剩约 4 GB；同时打开大量浏览器标签/Office 时可能卡顿，但不阻止演示。
- **规避方案**：演示机专用于 RAGFlow；关闭不必要的应用；把 WSL 内存设为 12 GB 并在启动后观察 `MemTotal` 与 `docker stats`。
- **后续动作**：若频繁 OOM，考虑升级内存或迁移到更高配置机器；第一版不采购云服务器。

## KI-005：在线模型 key 尚未配置

- **级别**：P2
- **状态**：待处理
- **现象**：仓库只有 `DASHSCOPE_API_KEY` 的占位约定，未配置真实 key；百炼账号额度与模型权限未验证。
- **新机复核（2026-10-18）**：仍未配置；本次交接按要求未读取、未配置任何真实 key。
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
- **证据**：旧机 `C:\RAG库\_tools\skill-atlas-update.log` 中的 traceback。
- **新机复核（2026-10-18）**：本次未安装、未运行 skill-atlas；不影响 RAGFlow。
- **影响**：无法一次性生成全量能力位索引；不影响 RAGFlow 选型与部署。
- **规避方案**：在本地工具副本 `api.py` 的重试异常中加入 `http.client.HTTPException`，并分多次 `enrich` 断点续跑；仅修改本机 `_tools` 副本，不改上游仓库。
- **后续动作**：如后续仍需完整索引，改用稳定网络或给工具提交上游 issue。

## KI-007：基础组件端口默认暴露到主机

- **级别**：P2（安全）
- **状态**：待处理
- **现象**：官方 compose 将 Elasticsearch 1200、MySQL 3306、MinIO 9000/9001、Valkey 6379 发布到主机所有网卡。
- **新机复核（2026-10-18）**：RAGFlow 容器尚未启动，无法检查实际监听地址；8080 当前空闲。
- **影响**：同一局域网内的其他机器可能访问数据库/对象存储；默认密码若未改风险更高。
- **规避方案**：
  1. `.env.example` 已强制使用 `CHANGE_ME_*`，部署时必须替换；
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
- **状态**：已知限制（第二步范围）
- **现象**：第一步只完成环境检查、配置拉取与文档；未执行 `docker compose pull/up`，未验证登录、模型调用、文档入库与引用。
- **证据**：旧机仅执行 `docker compose config --quiet` 校验，退出码 0；新机尚无 Docker，连语法校验也无法重跑。
- **新机复核（2026-10-18）**：仍未启动 RAGFlow，未拉镜像，未入库；本次交接未改变该状态。
- **影响**：部署步骤与资源调整尚未在真实容器中跑通，第二步可能出现未预见的问题。
- **规避方案**：第二步严格按 `docs/deployment.md` 执行，先关闭 KI-010、KI-002，再逐项记录实际结果；失败项回填本文件。
- **后续动作**：第二步完成后补充“实际启动验证”记录与截图（不含密钥）。

## KI-010：新机未安装 Docker Desktop，WSL2 未启用

- **级别**：P1（直接阻塞第二步）
- **状态**：**待处理（新发现）**
- **现象（2026-10-18 实测）**：
  - `docker --version`、`docker compose version` 均提示命令不存在；
  - `C:\Program Files\Docker\Docker\Docker Desktop.exe` 及 Docker CLI 常见路径不存在；
  - 注册表卸载项中无 Docker，Docker 服务、Docker 进程均不存在；
  - `Microsoft-Windows-Subsystem-Linux`、`VirtualMachinePlatform`、`Microsoft-Hyper-V-All`、`Containers` 功能均为 `Disabled`；
  - `wsl.exe` 仅有 Windows 收件箱版本 `10.0.19041.5794`，`wsl --status` 退出码 50，无 Linux 发行版，`wsl --version` 不可用；
  - CPU 虚拟化已在固件中启用（`VirtualizationFirmwareEnabled=True`，SLAT=True），具备启用 WSL2 的硬件条件。
- **影响**：没有 Docker/Compose 就无法拉取或启动 RAGFlow；第二步的全部工作被阻塞。
- **安装指引（本次交接未执行，需用户确认后再做）**：
  1. **先确认系统支持状态**：Windows 10 Pro 22H2（19045）在 Docker 官方列表中，但 Windows 10 常规支持已结束，见 KI-011。
  2. **启用并升级 WSL2**：管理员 PowerShell 执行 `wsl --install`，按提示重启；重启后执行 `wsl --update`；用 `wsl --version` 确认 ≥ 2.1.5。若 Microsoft Store 被策略阻断，可从 [WSL Releases](https://github.com/microsoft/WSL/releases) 下载最新稳定版 MSI 安装。
  3. **安装 Docker Desktop**：从 [Docker 官方 Windows 安装页](https://docs.docker.com/desktop/setup/install/windows-install/) 下载 x86_64 安装包，选择 **Use WSL 2 instead of Hyper-V**，完成安装后启动并接受许可。
  4. **验证 CLI**：`docker --version`、`docker compose version`、`docker info` 均应成功。
  5. **配置 VM 内存**：新建 `%UserProfile%\.wslconfig`，写入 `[wsl2]`、`memory=12GB`、`processors=6`、`swap=4GB`；`wsl --shutdown` 后重启 Docker Desktop，确认 `docker info` 的 `MemTotal` ≥ 12 GB。
  6. **复核**：执行 `wsl -d docker-desktop sysctl vm.max_map_count` 确认 ≥ 262144，再运行 `scripts/check-env.ps1 -Drive C`。
- **后续动作**：等待用户明确授权后安装；安装完成后把本项标记为“已解决”，并记录 Docker Desktop、Engine、Compose 版本。

## KI-011：Windows 10 22H2 已过常规支持期

- **级别**：P2（兼容性/安全）
- **状态**：**待处理（新发现）**
- **现象**：新机为 Windows 10 Pro 22H2，Build 19045.5854。Windows 10 22H2 的常规支持已于 2025-10-14 结束（除非另行购买 ESU）。
- **证据**：
  - 本机 `Win32_OperatingSystem`：`Microsoft Windows 10 专业版`，版本 `10.0.19045`，UBR `5854`；
  - Docker 官方 Windows 安装文档将 Windows 10 22H2（19045）列入支持范围，但同时注明只支持仍处于微软服务期内的 Windows 版本；
  - Microsoft Windows 生命周期：<https://learn.microsoft.com/lifecycle/products/windows-10-home-and-pro>。
- **影响**：系统不再获得常规安全更新；Docker Desktop 可能因超出微软服务期而不提供支持；演示机若接入企业网络，存在合规与安全风险。
- **规避方案**：
  1. 部署前确认该机是否有 ESU 或企业延长支持；
  2. 条件允许时升级到仍受支持的 Windows 11；
  3. 若只能使用当前系统，至少在演示期间断网/隔离，并记录为已接受风险；
  4. 安装 Docker 前复核官方当前系统要求，不要假设 Windows 10 一定可用。
- **后续动作**：在安装 Docker Desktop 前由用户确认系统支持策略；若升级系统，升级后重跑全部环境检查。
