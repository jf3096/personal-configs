---
name: structured-operation-summary
description: Use when you have completed debugging, configuration, or implementation work and need a review-ready structured summary with timeline, changes, evidence, risks, and verification status.
---

# Structured Operation Summary

## Overview

将一次任务执行结果整理为“可审阅、可复验、可追责”的结构化报告。

核心原则：
- 先事实，后结论。
- 先证据，后判断。
- 未验证必须显式标注原因。
- 默认脱敏敏感信息（token/password/apiKey/cookie）。

## When to Use

在以下场景使用：
- 修复 bug 后需要给出可审阅总结。
- 修改配置/服务后需要说明影响与验证。
- 代码改动后需要给出结构化交付说明。
- 需要把“我做了什么”转成“审阅者可快速判断质量”的结果。

不适用：
- 纯闲聊。
- 尚未执行任何实质操作，仅停留在想法阶段。

## Output Contract

默认按以下固定顺序输出：

1. **目标与结果**
2. **执行过程（时间线）**
3. **变更清单**
4. **验证证据**
5. **风险与回滚**
6. **可执行复验命令**
7. **最终状态行**

## Writing Rules

- 用绝对路径引用文件。
- 每条验证证据至少包含：`command`、`result`（或关键输出）。
- 报错引用格式：先英文原文，再中文解释。
- 不要把猜测写成事实；不确定内容用“推断”标识。
- 涉及时间时优先给绝对时间（例如 `2026-03-12 15:40 CST`）。

## Minimum vs Full Mode

### Minimum（快速审阅）
- 目标与结果
- 变更清单
- 验证证据（1-3条）
- 状态行

### Full（审计版）
- 使用完整 Output Contract 七段。
- 包含风险、回滚路径、复验命令。

## Quality Checklist

- 是否明确了目标与最终状态？
- 是否列出真实变更对象（文件/服务/配置）？
- 是否给出可执行验证证据？
- 是否标注未验证项和原因？
- 是否做了敏感信息脱敏？

## Common Mistakes

- 只写“已完成”，没有命令或输出证据。
- 混用相对路径，导致审阅者难以定位。
- 忽略失败闭环（失败 -> 修复 -> 再验证）。
- 泄露 token 或密钥。

## Template

使用模板：`references/report-template.md`

