# RAGFlow v0.27.2 官方 Compose 配置快照

本目录保存 RAGFlow 官方 `docker/` 目录中与部署直接相关的配置，用于评审与追溯。**运行时请以官方仓库完整目录为准**（还需要 `entrypoint.sh`、`init.sql`、`service_conf.yaml.template`、`nginx/` 等文件）。

## 1. 来源

| 项目 | 值 |
| --- | --- |
| 上游仓库 | <https://github.com/infiniflow/ragflow> |
| 版本标签 | `v0.27.2` |
| 标签 commit | `a024bea0cd93f39e6652a42bf84dd20c55bc560b` |
| 拉取时间 | 2026-10-17 |
| 许可证 | Apache-2.0 |

## 2. 文件与校验

| 文件 | 上游路径 | Git blob SHA-1 | 本地 SHA-256 | 是否原样 |
| --- | --- | --- | --- | --- |
| `docker-compose.yml` | `docker/docker-compose.yml` | `a88420c91af1d652eb31efbbbdfd4518d11d98f0` | `33E23CEA41F95E8854B10E128D89630043FDF253AA168EA667F49ECEE08D89BC` | 是 |
| `docker-compose-base.yml` | `docker/docker-compose-base.yml` | `751451035bfb7bc3e809e550d801216e8fcd5bd4` | `097DBF316C754C2A8B14492E93B5296439F3ADD08E1A416335C1123F65AC0033` | 是 |
| `.env.example` | 由 `docker/.env` 派生 | — | `22572C1B214B4918AC9621630CD781A4DD9EF243A14008141F7417061F97DA5E` | 否，已脱敏 |

`git hash-object docs/ragflow/docker-compose.yml` 的结果与上游 blob SHA-1 一致，可证明两个 compose 文件逐字节未改动。

`.env.example` 相对官方 `.env` 只有三类改动：

1. 所有默认密码替换为 `CHANGE_ME_*` 占位（官方默认值虽然是公开的 `infini_rag_flow`，但不适合直接沿用）；
2. `SVR_WEB_HTTP_PORT` 由 `80` 改为 `8080`，避免与 Windows 上可能存在的 80 端口服务冲突；
3. `MEM_LIMIT` 由 `8073741824`（约 7.5 GiB）改为 `6442450944`（6 GiB），适配本机 12 GB 的 WSL/Docker VM。

其余变量与注释保持官方原样。

## 3. 为什么固定 v0.27.2

- `v0.27.2` 是截至 2026-10-17 的最新**稳定**版本；
- 同日最新的 `v1.0.0-rc2` 仍是 release candidate，不用于演示环境；
- 固定小版本可避免 `latest` 漂移导致解析/引用行为变化。

## 4. 更新方法

```powershell
# 查看最新稳定版
gh api repos/infiniflow/ragflow/releases/latest --jq '.tag_name'

# 重新拉取指定标签的文件（示例：v0.27.2）
$tag = "v0.27.2"
gh api "repos/infiniflow/ragflow/contents/docker/docker-compose.yml?ref=$tag" --jq '.content'
```

更新后必须：

1. 重新计算 SHA-256 并更新本文件；
2. 对比 `.env.example` 的新增/删除变量；
3. 同步 `docs/deployment.md` 附录中的配置全文；
4. 在第二步重新执行 `docker compose config --quiet` 校验。

## 5. 注意

- 两个 compose 文件通过 `include` 组合，必须放在同一目录；
- 快照本身不足以启动整套服务（缺少入口脚本和初始化 SQL），部署时请克隆完整仓库；
- 本目录不包含任何真实密钥或企业内部资料。
