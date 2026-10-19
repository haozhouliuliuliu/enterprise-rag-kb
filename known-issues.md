# 已知问题清单

> 更新时间：2026-10-19
> 当前底座：**AnythingLLM Desktop v1.18.0**（原生 Windows，无 Docker/WSL2）
> 状态说明：`待处理` / `已规避` / `已解决` / `已知限制`
> 历史说明：KI-001～KI-011 保留 2026-10-17 RAGFlow/Docker 旧机证据；v0.2 底座变更后的结论单列，不删除旧记录。

## 汇总

| ID | 级别 | 问题 | 最新结论（2026-10-19） | 状态 |
| --- | --- | --- | --- | --- |
| KI-001 | P1 | C 盘可用空间低于 50 GB | 新机 C 盘 79.31 GB，已达标 | 已解决 |
| KI-002 | P1 | Docker VM 内存 7.43 GB，低于 12 GB | **已通过更换底座规避**：不再使用 Docker/WSL2/VM | 已规避 |
| KI-003 | P3 | Docker Desktop 未开机自启 | 已通过更换底座规避：不再使用 Docker | 已规避 |
| KI-004 | P2 | 物理内存 15.96 GB，略低于 16 GB | 仍低于 16 GB，但不再预留 12 GB Docker VM，影响显著降低 | 已知限制 |
| KI-005 | P2 | 百炼 API key 未配置 | 已配置并验证 `qwen-plus` / `text-embedding-v4` | 已解决 |
| KI-006 | P3 | skill-atlas 拉取数据 IncompleteRead | 仅辅助工具，不影响 AnythingLLM | 已规避 |
| KI-007 | P2 | Docker 基础组件端口暴露 | 已通过更换底座规避：仅本机 3001/8888 监听 | 已规避 |
| KI-008 | P3 | RAGFlow 管理密码不可改 | RAGFlow 专属问题，已随底座更换消失 | 已规避 |
| KI-009 | P3 | 尚未端到端启动验证 | workspace 创建、重启持久化、Developer API、SMOKE-01 均已通过 | 已解决 |
| KI-010 | P1 | 新机未安装 Docker Desktop/WSL2 | **已通过更换底座规避**：原生应用不依赖 Docker/WSL2 | 已规避 |
| KI-011 | INFO | Windows 10 22H2 已过常规支持期 | 原生应用不依赖 Docker 的系统支持期；降级为 INFO，安全补丁仍需关注 | 已知限制 |
| KI-012 | P2 | 从带 `ELECTRON_RUN_AS_NODE=1` 的 Shell 启动会误入 Node 模式 | 已定位；正常双击启动不受影响 | 已规避 |
| KI-013 | P1 | i7-3770 不支持 AVX2，LanceDB cosine 检索触发非法指令 | 已用本机 JS-cosine 补丁规避；升级后需重做 | 已规避 |
| KI-014 | P2 | 用户称已轮换 key，但本机文件/应用仍是上一轮 key | **已澄清：不轮换，以本机可用 key 为准** | 已解决 |
| KI-015 | P2 | 多文档综合题 sources 不完整，LLM 可能混淆型号通信版本 | 30 题中 4 道未命中；不阻塞验收线 | 待处理 |

---

## KI-001：C 盘空间不足

- **级别**：P1（旧机）
- **状态**：**已解决**
- **旧机（2026-10-17）**：C 盘可用 16.46 GB，D 盘 216.8 GB；低于 RAGFlow 50 GB 要求。
- **新机（2026-10-18）**：C 盘 150 GB，总可用 **79.31 GB**；D 盘可用 320.75 GB。`check-env.ps1 -Drive C` 判定 PASS。
- **结论**：C 盘已达标；AnythingLLM 安装到 D 盘，数据目录在 C 盘用户目录，当前余量足够。

## KI-002：Docker VM 内存不足

- **级别**：P1（旧机）
- **状态**：**已通过更换底座规避**
- **旧机（2026-10-17）**：Docker VM 12 CPU / 7.43 GB RAM，低于演示建议 12 GB；Elasticsearch 有 OOM 风险。
- **v0.2 变更（2026-10-18）**：废弃 RAGFlow + Docker，改用 AnythingLLM Desktop；不再创建 Docker VM，也不再运行 Elasticsearch/MySQL/MinIO/Valkey 容器。
- **结论**：旧问题不再适用，无需调整 `.wslconfig`；保留旧数据作历史。

## KI-003：Docker Desktop 未开机自启

- **级别**：P3
- **状态**：已通过更换底座规避
- **旧机现象**：检查开始时 Docker 引擎未运行，启动后约 15 秒就绪。
- **v0.2 变更**：不再使用 Docker Desktop；改为启动 `D:\RAG库\AnythingLLM\AnythingLLM.exe`。
- **后续**：如需开机自启，可为 AnythingLLM 创建启动快捷方式；当前不要求。

## KI-004：物理内存略低于官方建议

- **级别**：P2
- **状态**：已知限制（影响降低）
- **旧机**：15.34 GB；新机 **15.96 GB**（17,134,211,072 字节），仍比 16 GB 少约 0.04 GB。
- **v0.2 变化**：不再为 Docker/WSL 预留 12 GB；AnythingLLM 原生应用 + 在线模型模式内存压力明显降低。
- **影响**：同时打开大量浏览器标签、Office 或解析超大 PDF 时可能卡顿，但不阻止演示。
- **规避**：演示机专用；关闭无关应用；单次只处理一份大文档。

## KI-005：百炼 API key 未配置

- **级别**：P2
- **状态**：**已解决（2026-10-18）**
- **旧现象**：`DASHSCOPE_API_KEY` 未配置，无法调用模型。
- **处理结果**：
  1. key 已保存到仓库外 `C:\RAG库\secrets\dashscope.key`；
  2. DashScope 直连验证：`qwen-plus` chat 返回 200，`text-embedding-v4` 返回 **1024** 维向量；
  3. AnythingLLM 已保存 `LLM_PROVIDER=generic-openai`、`qwen-plus`、`EMBEDDING_ENGINE=generic-openai`、`text-embedding-v4`；
  4. 模型 key 保存在本机 `%APPDATA%\anythingllm-desktop\storage\.env`，未进入仓库。
- **安全提醒**：本次 key 曾通过聊天传递，建议演示结束后在百炼控制台轮换；不得写入仓库、截图或提交信息。

## KI-006：skill-atlas 拉取数据出现 IncompleteRead

- **级别**：P3
- **状态**：已规避
- **旧机现象**：`skill-atlas fetch/enrich` 拉取 GitHub 大响应时报 `http.client.IncompleteRead`。
- **v0.2**：未安装、未运行 skill-atlas；不影响 AnythingLLM。
- **后续**：如仍需要，使用稳定网络或分多次 enrich。

## KI-007：基础组件端口暴露

- **级别**：P2（旧机安全项）
- **状态**：已通过更换底座规避
- **旧机现象**：RAGFlow compose 将 ES 1200、MySQL 3306、MinIO 9000/9001、Valkey 6379 发布到主机所有网卡。
- **v0.2**：不再运行这些容器；AnythingLLM 仅监听 `127.0.0.1:3001`（应用/API）与 `127.0.0.1:8888`（collector）。
- **后续**：保持不添加公网端口映射；如需远程访问，先做安全评审。

## KI-008：RAGFlow 管理密码不可改

- **级别**：P3
- **状态**：已通过更换底座规避
- **旧机现象**：RAGFlow v0.27.2 管理界面暂不支持修改 `admin@ragflow.io` 密码。
- **v0.2**：不再使用 RAGFlow 管理界面，问题消失。
- **后续**：AnythingLLM 本机使用 Windows 账户与 Developer API key；仍建议专用演示账户。

## KI-009：尚未端到端启动验证

- **级别**：P3
- **状态**：**已解决（2026-10-18）**
- **已完成**：
  - AnythingLLM v1.18.0 安装到 D 盘，`127.0.0.1:3001` 监听；
  - 百炼 LLM/Embedding provider 配置并保存；
  - workspace `enterprise-rag-kb` 创建（id=2）；
  - 完全退出后重启，workspace 与 Developer API key 仍在（P1-07 通过）；
  - Developer API `GET /workspaces` 返回 2 个 workspace；
  - `SMOKE-01` 调用成功，回答 `EVAL_OK`，判定“命中”。
- **未覆盖**：真实文档上传后的 chunk/embedding/检索/引用链路，留到第三步资料入库时验证。
- **证据**：`docs/deployment.md` 第 6.3、8 节；`tests/results/eval-20261018-191433.md`。

## KI-010：新机未安装 Docker Desktop/WSL2

- **级别**：P1（旧机阻塞）
- **状态**：**已通过更换底座规避**
- **旧机现象**：Docker Desktop、Docker CLI、Compose 均不存在；WSL/VirtualMachinePlatform/Hyper-V 功能全部 Disabled。
- **v0.2 变更**：项目改用 AnythingLLM 原生 Windows 应用，不依赖 Docker/WSL2/Hyper-V。
- **结论**：安装前置条件从“先装 WSL2 + Docker Desktop”变为“直接安装 AnythingLLM”；本项不再阻塞。
- **历史**：旧机安装指引保留在 git 历史中，不再需要执行。

## KI-011：Windows 10 22H2 已过常规支持期

- **级别**：**INFO（降级）**
- **状态**：已知限制（不阻塞）
- **现象**：新机 Windows 10 Pro 22H2，Build 19045.5854；Windows 10 常规支持已于 2025-10-14 结束。
- **v0.2 结论**：AnythingLLM 是原生 Windows 应用，不依赖 Docker Desktop 对 Windows 服务期的要求，因此不再作为部署阻塞项；降级为 INFO。
- **仍需注意**：系统安全补丁、浏览器/应用兼容性仍需关注；如企业要求受支持 OS，建议升级 Windows 11。
- **后续**：演示机不接入不可信网络；定期检查安全更新。

## KI-012：`ELECTRON_RUN_AS_NODE=1` 导致启动失败

- **级别**：P2（仅特定 Shell 环境）
- **状态**：已规避
- **现象**：在设置了 `ELECTRON_RUN_AS_NODE=1` 的 PowerShell 中启动 `AnythingLLM.exe`，Electron 以 Node 模式运行，报 `bad option` 后退出；3001/9222 不监听。
- **证据**：`Get-ChildItem Env:` 显示 `ELECTRON_RUN_AS_NODE=1`；清除后应用正常启动，出现 4 个 Electron 进程并监听 3001。
- **影响**：仅影响从该 Shell 启动的场景；普通双击启动不受影响。
- **规避**：启动前执行 `Remove-Item Env:ELECTRON_RUN_AS_NODE`，或从开始菜单/快捷方式启动。详见 `docs/deployment.md` 排障。

## KI-013：i7-3770 缺少 AVX2，LanceDB cosine 检索崩溃

- **级别**：P1（本机检索阻塞）
- **状态**：**已规避（本机补丁）**
- **现象**：调用 `/api/v1/workspace/.../vector-search` 或 `/chat` 时，AnythingLLM 后端进程直接退出，端口 3001 消失；日志无异常堆栈。
- **根因**：LanceDB 官方要求 x86 平台支持 AVX2；本机 Intel Core i7-3770 仅有 AVX，不支持 AVX2。直接调用 LanceDB `vectorSearch(...).distanceType("cosine")` 返回 `0xC000001D`（非法指令）；默认 L2 检索可执行。
- **证据**：Node 直接执行 cosine 检索退出码 `-1073741795`；L2 检索正常；LanceDB issue #1437 明确说明 AVX2 要求。
- **影响**：不修补则无法用 AnythingLLM 检索，无法完成引用验收。
- **规避**：
  1. 本机将 `resources\backend\server.js` 的 LanceDB `similarityResponse` 改为读取表行、在 Node 中计算 cosine（22 条向量，开销可忽略），不再调用原生 cosine 检索；
  2. workspace `similarityThreshold=0.0`、`topN=5`；
  3. 原文件备份：`D:\RAG库\backup\server.js.original-20261018-182358`；
  4. 该补丁仅对本机有效，AnythingLLM 升级会覆盖，需重新评估/应用。
- **验证**：5 道抽查题 Top-5 检索 5/5 命中，回答 5/5 命中。
- **后续**：若换到支持 AVX2 的机器，优先恢复上游原生 cosine 检索，不保留该补丁。

## KI-014：key 轮换状态误判

- **级别**：P2（安全/配置一致性）
- **状态**：**已解决（2026-10-19 澄清）**
- **原现象**：曾记录“用户称已轮换 key，但本机文件仍是上一轮值”。
- **澄清结论**：用户明确 **key 不做轮换，以本机当前可用的 key 为权威版本**：
  - `C:\RAG库\secrets\dashscope.key`
  - `C:\RAG库\secrets\anythingllm_api.key`
- **证据**：Developer API 200、DashScope chat 200、SMOKE-01 与 5 题抽查均通过；本机文件即为权威版本。
- **影响**：无；不再作为阻塞项。
- **后续**：所有步骤不得再因 key 轮换问题阻塞；如未来对外暴露/导入真实资料，再按 `docs/security.md` 2.4 的条件轮换。

## KI-015：多文档综合题的检索/引用不稳定

- **级别**：P2（质量风险，不阻塞当前验收线）
- **状态**：待处理
- **现象（30 题全量）**：
  - M01、C05：检索未返回 X-100 产品说明书，回答把 X-100 的 Bluetooth 5.0 写成 5.2；
  - M03、C01：回答数值正确，但 API `sources[]` 未包含目标文档（M03 缺 QS V2.1，C01 缺 X-100 说明书）；
  - C04 在第 1/2 轮把 X-100 量程答成 1–100/5–200，第 3 轮强化提示词后修正为 0.5–100。
- **影响**：Top-5 检索与来源支持均为 84%（达到 80% 线），但综合/易混淆题仍有 4 道未命中；引用映射不可靠。
- **规避/后续**：
  1. 对多文档问题拆分查询或引入 rerank，确保两份目标文档都进入 Top-5；
  2. 评估更强对话模型或按型号/版本分 workspace；
  3. 继续调小 chunk 或改进表格/型号文档结构；
  4. 评测结果不得只看最终命中率，需保留逐题归因。
- **证据**：`tests/results/full-30-summary.md`、`tests/results/eval-20261019-111954.md`。
