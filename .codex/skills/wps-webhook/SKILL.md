---
name: wps-webhook
description: Use when sending WPS webhook robot messages, managing named WPS webhook targets, switching the default WPS webhook target, or working from the WPS webhook robot documentation
---

# WPS Webhook

## Overview

Use this skill for two things only:

- Send WPS webhook robot messages.
- Manage the global WPS webhook target config.

**Reference:** Read `references/wps-webhook-doc-notes.md` before building payloads.

When talking to non-technical users, explain `target` in plain language:

- `target` = the name or alias for one saved WPS webhook URL
- `default_target` = the saved target used when the user does not name one explicitly
- `config.json` = the saved list of webhook aliases and their real webhook URLs

## When to Use

Use this skill when the user asks to:

- send a WPS group robot message
- send `text`, `markdown`, `link`, or `card` content to WPS
- add, update, remove, or inspect a named webhook target
- switch the default WPS webhook target

Do not use this skill for non-WPS webhooks or for building a standalone webhook service.

## Global Config

Config file:

`/home/jf3096/.codex/wps-webhook/config.json`

Expected shape:

```json
{
  "default_target": "ops",
  "targets": {
    "ops": {
      "webhook_url": "https://xz.wps.cn/api/v1/webhook/send?key=xxxx"
    }
  }
}
```

Rules:

- `default_target` is optional.
- If `default_target` is missing, sending requires an explicit `target`.
- `targets` must be an object keyed by alias.
- Each target must contain `webhook_url`.
- Preserve unrelated targets on every config edit.
- Never guess or synthesize a missing webhook URL.

User-facing explanation:

- Say "saved group name", "alias", or "send target" before falling back to raw `target` jargon.
- Explain `config.json` as a saved address book for WPS webhook destinations.
- Prefer "register a group named `ai群聊`" over "add a target" when the user sounds non-technical.

## Workflow

### A. Send Message

1. Read the global config file.
2. Resolve the target from explicit input first, then `default_target`.
3. Stop if the config file, target, or `webhook_url` is missing.
4. Build one documented WPS payload only: `text`, `markdown`, `link`, or `card`.
5. Send a real HTTP `POST` request to the configured webhook URL.
6. Report observable evidence: request type, target, status code, and response summary.

### B. Manage Config

1. Read the current config file if it exists.
2. If it does not exist, create the minimal valid JSON only when the user supplied enough data.
3. Apply only the requested mutation: add target, update target, remove target, or switch `default_target`.
4. Keep unrelated targets unchanged.
5. Validate that the final file is valid JSON before finishing.

## How To Explain It

Use this mental model when the user asks what the config means:

- `webhook_url` is the real destination address.
- `target` is the label for that address, like a contact name in an address book.
- `config.json` stores all saved labels and the default one.

Prefer concrete wording such as:

- "先登记一个群，名字叫 `ai群聊`，以后就可以直接说给 `ai群聊` 发消息。"
- "如果你不指定群，就会发到默认登记的那个群。"

## Safety Rules

- Do not send a message if the target does not exist.
- Do not replace the whole config with a single target unless the user explicitly requests that destructive change.
- Do not rename payload fields away from the WPS document.
- Do not claim delivery success without a real HTTP result.
- Do not use theoretical-success wording for undelivered messages; report them as unverified.

## Verification

- After config edits, parse the JSON and confirm the requested fields are present.
- After send attempts, capture HTTP status and response body summary.
- If no real webhook is available, say the send was not verified.

## Common Requests

- "新增一个 finance target" -> edit the config file incrementally.
- "登记一个群，名字叫 `ai群聊`，webhook 是 https://..." -> create or update one saved alias in the config.
- "把默认 target 切到 ops" -> update `default_target` only.
- "把默认群改成 `ai群聊`" -> update `default_target` only, using user-facing wording.
- "发一条 markdown 到 ops" -> resolve `ops`, build the documented markdown payload, send it, and report evidence.
- "给 `ai群聊` 发一句 hi" -> resolve the saved alias `ai群聊`, send the message, and report evidence.
