# 模拟企业资料

本目录用于存放**虚构**的企业资料源文件（PDF/Word）及其骨架清单。

## 强制声明

- 全部使用虚构公司名、虚构产品型号和虚构数据。
- 公司“星澜精密制造（虚构）有限公司”、品牌“星澜 / STARLANE”均为虚构。
- 禁止放入真实公司名称、客户信息、真实工艺参数、图纸、检验记录或其他敏感信息。
- 如与真实企业或产品雷同，纯属巧合。
- 本目录资料不得用于真实生产、检验、采购或安全决策。

## 当前内容

| 路径 | 说明 | 状态 |
| --- | --- | --- |
| [catalog.txt](catalog.txt) | 资料骨架清单：三份资料的章节、检验指标与数值标准 | ✅ 已完成 |
| `product/STAR-NX200-manual-v0.1.pdf` | a) NX-200 智能数显扭矩扳手说明书 | ⏳ 第二步制作 |
| `quality/STAR-QS-001-inspection-spec-v0.1.docx` | b) 质量检验规范（含具体指标） | ⏳ 第二步制作 |
| `equipment/STAR-EQ-003-operation-manual-v0.1.pdf` | c) EQ-003 自动锁付单元操作手册 | ⏳ 第二步制作 |

详细章节、指标表和测试覆盖见 [catalog.txt](catalog.txt)。

## 目录结构

```text
data/
├── catalog.txt
├── README.md
├── product/      # 产品说明书
├── quality/      # 质量检验规范
└── equipment/    # 设备操作手册
```
