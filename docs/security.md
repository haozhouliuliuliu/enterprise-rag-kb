# 安全基线（AnythingLLM 桌面版）

> 版本：v0.2（2026-10-18）
> 适用阶段：底座部署与评测通道
> 适用范围：单台企业内部 Windows 演示机

## 1. 安全目标与边界

本项目的目标是**用虚构资料验证 RAG 引用闭环**，不是生产级知识库。安全边界如下：

- 应用运行在本机 Windows 账户下，仅监听 `127.0.0.1`；
- 向量化与回答生成使用阿里云百炼外部 API；
- 不接入公网、不做端口映射、不部署本地大模型；
- 只使用虚构资料，不导入真实企业数据；
- API key 只存在于本机未跟踪配置或本机应用数据库中。

## 2. API 密钥管理

| 密钥 | 用途 | 存放位置 | 是否入仓库 |
| --- | --- | --- | --- |
| `DASHSCOPE_API_KEY` | 百炼 `qwen-plus` 与 `text-embedding-v4` | AnythingLLM 保存在 `%APPDATA%\anythingllm-desktop\storage\.env`；仓库外另有 `C:\RAG库\secrets\dashscope.key` | **禁止** |
| `ANYTHINGLLM_API_KEY` | 调用本机 Developer API（评测脚本） | `C:\RAG库\secrets\anythingllm_api.key` + 仓库根目录 `.env`（已忽略） | **禁止** |
| 其他数据库/对象存储密码 | 本项目不再使用 RAGFlow/Docker，无此类密码 | — | — |

### 2.1 百炼模型 key

1. 在阿里云百炼控制台创建 key，确认 `qwen-plus`、`text-embedding-v4` 可用；
2. 在 AnythingLLM **Settings → Model providers** 中录入，不写入 README、脚本或截图；
3. key 保存在本机 `%APPDATA%\anythingllm-desktop\storage\.env`，依赖 Windows 账户权限保护；该文件是明文配置，演示机应启用 BitLocker；
4. 不在聊天、日志、录屏、提交信息中出现完整 key；
5. 本次 key 曾通过聊天传递，建议演示结束后在百炼控制台**吊销并重建**。

### 2.2 AnythingLLM Developer API key

1. 在 AnythingLLM **Settings → Developer API** 中启用并生成；
2. 本次已生成名称 `eval-local` 的 key，保存到 `C:\RAG库\secrets\anythingllm_api.key` 与仓库根目录 `.env`；
3. `tests/eval.py` 从 `ANYTHINGLLM_API_KEY` 环境变量或仓库根目录 `.env` 读取；
4. `.env` 已被 `.gitignore` 忽略，禁止 `git add -f`；
5. 如泄露，在 Developer API 设置中撤销并重新生成；本次 key 曾在自动化输出中出现，建议演示前轮换一次。

### 2.3 提交前检查

```powershell
git status --short
git diff --cached
git diff --cached | Select-String -Pattern 'sk-|DASHSCOPE|ANYTHINGLLM_API_KEY|Bearer '
```

发现任何真实 key，立即从暂存区移除并轮换；不要只依赖 `.gitignore`。

## 3. 数据分类与使用约束

**允许**：

- `data/catalog.txt` 中定义的虚构公司、虚构型号、虚构参数；
- 由这些虚构内容制作的 PDF/Word；
- 测试问题与测试结果（不含密钥、不含真实企业信息）。

**禁止**：

- 真实公司名称、客户名单、合同、报价、图纸、工艺配方；
- 真实检验记录、员工个人信息、身份证号、手机号、邮箱；
- 真实 API key、数据库密码、内网地址、VPN 配置；
- 任何标注“内部/机密/受控”的文件。

> 本项目的资料仅用于演示，不得用于真实生产、检验、采购或安全决策。

## 4. 数据流向外部服务

```text
本机 PDF/Word
  → 本机解析/切片
  → chunk 文本 → 阿里云百炼 text-embedding-v4（HTTPS 443）
  → 本机 LanceDB 向量索引

用户问题
  → 阿里云百炼 text-embedding-v4（HTTPS 443）
  → 本机检索 Top-N chunks
  → 问题 + chunks → 阿里云百炼 qwen-plus（HTTPS 443）
  → 回答 + 本机 chunk 引用
```

**必须向使用者明示**：

1. 文档切片和问答内容会发送至百炼（阿里云）外部服务；
2. 原始文件留在本机，但其中的文本内容会离开本机；
3. 因此只允许虚构资料；
4. 如企业要求数据不出内网，本方案不适用，需改为本地模型/本地 embedding，超出第一版范围。

## 5. 遥测与日志

- AnythingLLM 默认启用匿名遥测（启动、工作区创建、聊天等事件），可能发送到 Mintplex Labs；
- **本次已在 Settings → Privacy 关闭匿名遥测**，应用写入 `storage\.env` 的 `DISABLE_TELEMETRY='true'`；
- 应用日志位于 `%APPDATA%\anythingllm-desktop\storage\logs`，禁止把完整日志直接提交仓库；
- 提交测试结果前，检查回答与来源中是否混入真实数据或 key。

## 6. 本机加固

1. 使用专用 Windows 账户运行演示，不共用管理员日常账户；
2. 启用 BitLocker 或等价磁盘加密；
3. 仅监听 `127.0.0.1`，不添加公网端口映射；
4. 演示结束退出 AnythingLLM，必要时锁定屏幕；
5. 不安装来源不明的插件、模型或浏览器扩展；
6. 定期更新 AnythingLLM 与 Windows 安全补丁（Windows 10 已过常规支持期，见 KI-011）。

## 7. 事故处理

| 事件 | 处理 |
| --- | --- |
| 模型 key 疑似泄露 | 百炼控制台吊销 → 重建 → 更新 AnythingLLM → 复查日志/截图 |
| Developer API key 泄露 | AnythingLLM 设置中撤销 → 重新生成 → 更新本机 `.env` |
| 误传真实资料 | 立即从工作区删除文档与向量 → 清理本机数据目录 → 评估是否需要上报 |
| 仓库误提交 key | 立即轮换 key → 从 Git 历史移除（需重写历史并通知协作者）→ 复查远端 |
| 发现异常外联 | 断网 → 检查 AnythingLLM 设置与日志 → 保留证据 → 重置 key |

## 8. 验收检查清单

- [ ] `DASHSCOPE_API_KEY` 未出现在 `git log -p`、README、脚本、截图；
- [ ] `ANYTHINGLLM_API_KEY` 只在本机 `.env`/环境变量；
- [ ] `.env` 被 `git status` 忽略；
- [ ] 工作区只有虚构资料；
- [ ] AnythingLLM 只监听 `127.0.0.1`；
- [ ] 已向使用者说明 chunk 与问题会发送到阿里云百炼；
- [ ] 遥测已关闭或记录为已接受风险；
- [ ] 测试结果不包含密钥与真实企业信息。
