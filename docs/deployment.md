# AnythingLLM Desktop 部署与验证手册（Windows）

> 适用版本：**AnythingLLM Desktop v1.18.0**
> 适用环境：Windows 10/11 x64，原生应用，**不需要 Docker/WSL2**
> 模型：阿里云百炼 `qwen-plus` + `text-embedding-v4`
> 文档状态：安装已完成；模型连接、workspace、Developer API、持久化验证按本文执行并回填结果。

## 1. 本机实际环境

| 项目 | 实测值 |
| --- | --- |
| 操作系统 | Windows 10 Pro 22H2，Build 19045.5854，64 位 |
| CPU | Intel Core i7-3770，4 核 8 线程，3.40 GHz |
| 物理内存 | 15.96 GB（17,134,211,072 字节） |
| C 盘 | 150 GB，总可用 79.31 GB |
| D 盘 | 326.93 GB，总可用 320.75 GB |
| AnythingLLM | v1.18.0，安装于 `D:\RAG库\AnythingLLM` |
| 数据目录 | `C:\Users\Administrator\AppData\Roaming\anythingllm-desktop` |
| 本机服务 | `127.0.0.1:3001`（Web/API）、`127.0.0.1:8888`（collector） |
| Docker/WSL2 | 未安装、未启用；本项目**不需要** |
| 8080 | 空闲；本项目不使用 |

> Windows 10 22H2 已过常规支持期（KI-011，INFO）。AnythingLLM 原生应用不依赖 Docker Desktop 的系统服务期，但仍建议演示机保持隔离并关注安全更新。

## 2. 安装包与签名

| 项目 | 值 |
| --- | --- |
| 官方发布页 | <https://github.com/Mintplex-Labs/anything-llm/releases/tag/v1.18.0> |
| 安装包 | `AnythingLLMDesktop.exe` |
| 保存路径 | `D:\RAG库\installers\AnythingLLMDesktop-v1.18.0.exe` |
| 大小 | 407,381,240 字节（约 388.5 MiB） |
| SHA-256 | `B572DC48FBF6967BD3D7A408468FBDB7AA3ADBC75D90FC52421385FD1A799E5E` |
| 数字签名 | 有效；Signer `CN=Mintplex Labs Inc`，Issuer `DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1` |

校验命令：

```powershell
Get-FileHash 'D:\RAG库\installers\AnythingLLMDesktop-v1.18.0.exe' -Algorithm SHA256
Get-AuthenticodeSignature 'D:\RAG库\installers\AnythingLLMDesktop-v1.18.0.exe' |
  Select-Object Status, StatusMessage, @{n='Signer';e={$_.SignerCertificate.Subject}}
```

## 3. 安装到 D 盘

安装器为 NSIS，支持 `/S` 静默安装与 `/D=` 指定目录。`/D=` 必须是最后一个参数。

```powershell
$installer = 'D:\RAG库\installers\AnythingLLMDesktop-v1.18.0.exe'
$target = 'D:\RAG库\AnythingLLM'
Start-Process -FilePath $installer -ArgumentList '/S', "/D=$target" -Wait
```

验证：

```powershell
Get-Item 'D:\RAG库\AnythingLLM\AnythingLLM.exe' |
  Select-Object FullName, Length, @{n='Version';e={$_.VersionInfo.ProductVersion}}
Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*' |
  Where-Object { $_.DisplayName -like 'AnythingLLM*' } |
  Select-Object DisplayName, DisplayVersion, UninstallString
```

实测结果：

- 安装目录：`D:\RAG库\AnythingLLM`；
- 主程序：`D:\RAG库\AnythingLLM\AnythingLLM.exe`（约 172.5 MiB）；
- 注册表显示 `AnythingLLM 1.18.0`；
- 安装器没有把应用装到 `%LOCALAPPDATA%\Programs`。

## 4. 启动

正常启动：

```powershell
Start-Process 'D:\RAG库\AnythingLLM\AnythingLLM.exe'
```

首次启动会进入 onboarding，并自动创建数据目录：

```text
C:\Users\Administrator\AppData\Roaming\anythingllm-desktop\
└── storage\
    ├── anythingllm.db
    ├── documents\
    ├── lancedb\
    ├── hotdir\
    ├── logs\
    ├── models\
    └── .env                 # 本机模型配置（含 key，禁止提交）
```

检查服务：

```powershell
Get-NetTCPConnection -State Listen |
  Where-Object { $_.LocalPort -in 3001, 8888 } |
  Select-Object LocalAddress, LocalPort, OwningProcess
Invoke-WebRequest 'http://127.0.0.1:3001/api/ping' -UseBasicParsing
```

> **启动排障**：如果从设置了 `ELECTRON_RUN_AS_NODE=1` 的 Shell 启动，Electron 会以 Node 模式运行并报 `bad option` 后退出。先执行 `Remove-Item Env:ELECTRON_RUN_AS_NODE`，或从开始菜单/快捷方式启动。见 KI-012。

## 5. 配置百炼模型

### 5.1 准备 key

1. 登录阿里云百炼控制台，创建 API key；
2. 确认 `qwen-plus` 与 `text-embedding-v4` 可用；
3. 不要写入仓库；直接填入 AnythingLLM 设置界面。

### 5.2 LLM（对话模型）

在 onboarding 或 **Settings → Model providers** 中选择 **Generic OpenAI**，填写：

| 字段 | 值 |
| --- | --- |
| Base URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| API Key | 百炼 `DASHSCOPE_API_KEY` |
| Selected Model | `qwen-plus` |
| Model context window | `131072` |
| Max Tokens | `1024` |

### 5.3 Embedding（向量模型）

在 **Settings → Model providers → Embedding** 中选择 **Generic OpenAI**，填写：

| 字段 | 值 |
| --- | --- |
| Base URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| API Key | 同一把百炼 key |
| Embedding Model | `text-embedding-v4` |

保存后点击连接/验证按钮，确认没有 401/404。模型 key 保存在本机应用数据目录，**不进入 Git**。

### 5.4 连接验证（本次实测）

2026-10-18 已完成以下验证：

| 验证 | 结果 |
| --- | --- |
| DashScope chat（`qwen-plus`） | HTTP 200，返回 chat completion |
| DashScope embedding（`text-embedding-v4`） | HTTP 200，返回 **1024** 维向量 |
| AnythingLLM LLM provider | 已保存 `LLM_PROVIDER='generic-openai'`、`qwen-plus` |
| AnythingLLM Embedding provider | 已保存 `EMBEDDING_ENGINE='generic-openai'`、`text-embedding-v4`、chunk 8192、并发 20 |
| AnythingLLM 聊天 | workspace 显示 `qwen-plus`，SMOKE-01 返回 `EVAL_OK` |

模型 key 保存在本机 `%APPDATA%\anythingllm-desktop\storage\.env`（应用生成），不进入仓库。

> 真正的“上传文档 → chunk embedding → 检索 → 引用”端到端验证在第三步资料入库后执行；本次仅验证模型 API 与配置。

## 6. 创建 workspace 与持久化验证（P1-07）

### 6.1 创建

在 AnythingLLM 主界面创建 workspace，名称：

```text
enterprise-rag-kb
```

也可以通过 Developer API 创建（先完成第 7 节）：

```powershell
$headers = @{ Authorization = "Bearer $env:ANYTHINGLLM_API_KEY"; 'Content-Type' = 'application/json' }
$body = @{ name = 'enterprise-rag-kb' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:3001/api/v1/workspace/new' -Headers $headers -Body $body
```

### 6.2 持久化步骤

1. 确认 workspace 存在，记录 `slug`；
2. 完全退出 AnythingLLM（托盘退出或 `Browser.close`，不要只关闭窗口）；
3. 等待所有 `AnythingLLM.exe` 进程结束；
4. 重新启动应用；
5. 再次查询 workspace 列表，确认 `enterprise-rag-kb` 仍存在；
6. 记录数据目录与 `anythingllm.db` 的路径、时间戳。

### 6.3 实测结果（P1-07）

**结论：通过。重启应用后 workspace 仍存在。**

| 项目 | 实测值 |
| --- | --- |
| workspace | `enterprise-rag-kb` |
| workspace id | `2` |
| slug | `enterprise-rag-kb` |
| 创建时间 | `2026-10-18T09:46:50.990Z`（界面显示 17:46） |
| 数据目录 | `C:\Users\Administrator\AppData\Roaming\anythingllm-desktop\storage` |
| SQLite | `anythingllm.db`，397,312 字节，重启前最后写入 2026-10-18 17:46:50 |
| 重启前 API | `GET /api/v1/workspaces` 返回 2 个 workspace |
| 退出方式 | CDP `Browser.close`；8 个 `AnythingLLM.exe` 进程全部结束，3001/8888/9222 停止监听 |
| 重启后 API | `GET /api/v1/workspaces` 仍返回 `enterprise-rag-kb` |
| 校验结果 | `P1_07_WORKSPACE_EXISTS=1` |

重启后 Developer API key 仍然有效，说明 `api_keys` 表与 workspace 元数据均已持久化。

## 7. 启用 Developer API

**本次已完成**：在 **Settings → Developer API** 生成 key，名称 `eval-local`。key 只保存在本机：

- `C:\RAG库\secrets\anythingllm_api.key`（仓库外）
- 仓库根目录 `.env`（已被 `.gitignore` 忽略）

完整 key 不在本文、Git 或测试结果中。

1. 打开 AnythingLLM **Settings → Developer API**；
2. 启用 Developer API；
3. 生成 API key（只展示一次）；
4. 保存到本机密码管理器或仓库根目录 `.env`：

```dotenv
ANYTHINGLLM_BASE_URL=http://127.0.0.1:3001/api/v1
ANYTHINGLLM_WORKSPACE_SLUG=enterprise-rag-kb
ANYTHINGLLM_API_KEY=REPLACE_WITH_DEVELOPER_API_KEY
```

`.env` 已被 `.gitignore` 忽略，禁止提交。验证：

```powershell
$headers = @{ Authorization = "Bearer $env:ANYTHINGLLM_API_KEY" }
Invoke-RestMethod 'http://127.0.0.1:3001/api/v1/workspaces' -Headers $headers
```

预期返回 `workspaces` 数组。实测返回 2 个 workspace：`我的工作区` 与 `enterprise-rag-kb`。API key 不是百炼模型 key，两者不要混用。

## 8. 运行评测通道

```powershell
python tests/eval.py --validate-only
python tests/eval.py --id SMOKE-01
```

脚本调用：

```text
POST /api/v1/workspace/{slug}/chat
Authorization: Bearer <ANYTHINGLLM_API_KEY>
{
  "message": "这是评测通道连通性测试。请只回复：EVAL_OK",
  "mode": "chat"
}
```

结果写入 `tests/results/eval-*.json` 和 `.md`，包含回答、sources 与判定。完整题集在资料入库后补入 `questions.v0.2.json`。

**本次实测（2026-10-18 17:56:48，含 Top-5 检索统计）：**

- 题号：`SMOKE-01`
- 回答：`EVAL_OK`
- 判定：**命中**
- 汇总：命中 1 / 未命中 0 / 拒答 0 / 编造 0 / 错误 0；前 5 条检索可评估 0、命中 0
- 结果文件：`tests/results/eval-20261018-175648.md`、`tests/results/eval-20261018-175648.json`
- 说明：占位题用于验证 API 通道，未设置 `expected_sources`，因此不触发检索；正式检索/引用评测在第三步。

## 9. 验收清单

- [x] AnythingLLM v1.18.0 安装到 D 盘；
- [x] 安装包签名与 SHA-256 已记录；
- [x] 应用启动，`127.0.0.1:3001` 监听，数据目录已生成；
- [x] 百炼 `qwen-plus` chat 与 `text-embedding-v4` embedding 直连验证（1024 维）；
- [x] AnythingLLM LLM/Embedding provider 配置并保存；
- [x] workspace `enterprise-rag-kb` 创建；
- [x] 重启后 workspace 仍存在（P1-07）；
- [x] Developer API 启用并成功调用；
- [x] 匿名遥测已关闭（`DISABLE_TELEMETRY='true'`）；
- [x] 占位题返回 `EVAL_OK` 并记录结果；
- [ ] 上传文档后的真实 embedding/检索链路（第三步）；
- [ ] 14+ 题正式评测（第三步）。

## 10. 日常运维

```powershell
# 查看进程与端口
Get-Process AnythingLLM
Get-NetTCPConnection -State Listen | Where-Object LocalPort -in 3001,8888

# 数据目录
explorer "$env:APPDATA\anythingllm-desktop\storage"

# 备份（先退出应用）
Copy-Item "$env:APPDATA\anythingllm-desktop\storage" "D:\RAG库\backup\anythingllm-storage-$(Get-Date -Format yyyyMMdd)" -Recurse
```

- 备份至少包含 `storage\anythingllm.db`、`storage\documents`、`storage\lancedb`；
- 备份可能包含虚构资料与模型 key 的本地配置，禁止提交仓库；
- 卸载应用不会自动删除数据目录；
- 不执行任何会删除 `storage` 的“清理”脚本。

## 11. 故障排查

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 双击无窗口/进程秒退 | Shell 设置了 `ELECTRON_RUN_AS_NODE=1` | 清除该环境变量，或从开始菜单启动 |
| 3001 不监听 | 应用未完成启动、端口被占用 | 看 `storage\logs\backend-*.log`；`Get-NetTCPConnection -LocalPort 3001` |
| 模型验证 401 | key 错误/欠费/权限不足 | 核对百炼 key、模型权限与余额 |
| 模型验证 404 | Base URL 或模型名错误 | 使用 `.../compatible-mode/v1` 与 `qwen-plus` |
| Embedding 失败 | 模型名/维度不匹配 | 确认 `text-embedding-v4`；查看日志中的 400 详情 |
| 回答无 sources | 文档未解析、未命中、Top-N 太小 | 检查 chunk、调大 Top-N、降低相似度阈值 |
| 重启后 workspace 消失 | 数据目录被清理或换了 Windows 用户 | 确认 `%APPDATA%\anythingllm-desktop\storage` 未被删除 |
| 应用日志中出现 key | 误把 key 写进配置/脚本 | 立即轮换 key，清理日志，见 security.md |

## 12. 相关文档

- [architecture.md](architecture.md)：架构、数据流、外部服务边界
- [security.md](security.md)：密钥、虚构数据、遥测
- [README.md](../README.md)：ADR-001 与选型
- [known-issues.md](../known-issues.md)：已知问题
