# P1-05 文档更新测试记录（2026-10-19）

## 测试对象

- 测试文档：`tests/fixtures/STARLAN-X300-product-manual-v1.0.docx`
- 标题：X-300 便携式扭矩校验仪产品说明书（P1-05 测试文档）
- 独特数值：**额定功率 15 W**
- 文档页脚：含星澜精密仪器（虚构）有限公司虚构声明
- 说明：该文件仅作测试 fixture，不加入 `data/manifest.json`，不破坏 22 份正式资料清单，也不使用 X-900 / 《环境试验细则》。

## 基线

- workspace：`enterprise-rag-kb`
- 文档数：22
- chunk 数：**29**
- chunk size / overlap：1000 / 100
- Top-N：5（测试时）

## a) 新增后 chunk 数 29→30

- 上传接口：`POST /api/v1/document/upload/product`
- workspace：`enterprise-rag-kb`
- 上传后 workspace 文档数：**23**
- 上传后 chunk 数：**30**
- 新增文档 chunk：**1**
- 结果：**通过**

## b) 新文档事实命中

问题：

> X-300 的额定功率是多少？

回答摘要：

> X-300 的额定功率是 **15 W**。依据：《X-300 便携式扭矩校验仪产品说明书》，文件编号 STARLAN-PM-X300-TEST，版本 V0.1，发布日期 2026-10-19，第2节“主要参数”表格。

引用来源：

- X-300 产品说明书

判定：**命中**（关键词 15 W + 来源 X-300 产品说明书）。  
原始结果：`tests/results/eval-20261019-114025.json/.md`

## c) 删除后 chunk 数 30→29

- 删除方式：`POST /api/v1/workspace/enterprise-rag-kb/update-embeddings`，`deletes` 指定 X-300 的 docpath。
- 删除后 workspace 文档数：**22**
- 删除后 chunk 数：**29**
- 处理后的 X-300 JSON 缓存文件已从 `storage/documents/product/` 移除（系统级 `remove-document` 返回 404，未使用）。
- 结果：**通过**

## d) 删除后再次提问应拒答

同一问题：

> X-300 的额定功率是多少？

回答摘要：

> **资料不足。** 提供的所有 CONTEXT 中**未出现“X-300”型号**，也无任何关于 X-300 的产品说明书、检验规范、物料清单或技术参数文档……因此，无法确定 X-300 的额定功率。

判定：**拒答**（出现“资料不足”，未编造 15 W 或其他数值）。  
原始结果：`tests/results/eval-20261019-114057.json/.md`

## 结论

| 验证项 | 结果 |
| --- | --- |
| a) 新增后 29→30 chunk | ✅ |
| b) 新文档 15 W 命中且引用正确 | ✅ |
| c) 删除后 30→29 chunk | ✅ |
| d) 删除后 Query 模式拒答 | ✅ |

**P1-05 通过。**

## 备注

- 删除后 chunk 数回到 29，22 份正式文档与 `data/manifest.json` 未被污染。
- 测试 fixture 保留在 `tests/fixtures/` 作为可复现证据。
- 本次测试使用 X-300，不涉及 X-900 或《环境试验细则》。
