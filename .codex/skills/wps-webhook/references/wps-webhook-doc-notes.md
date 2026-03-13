# WPS Webhook Doc Notes

Source crawled on 2026-03-10 from:

- `https://365.kdocs.cn/3rd/open/documents/app-integration-dev/guide/robot/webhook`

## Endpoint

- Send URL pattern:
  - `https://xz.wps.cn/api/v1/webhook/send?key=...`
- Method:
  - `POST`

## Message Types

### Text

```json
{
  "msgtype": "text",
  "text": {
    "content": "..."
  }
}
```

### Markdown

```json
{
  "msgtype": "markdown",
  "markdown": {
    "text": "..."
  }
}
```

### Link

```json
{
  "msgtype": "link",
  "link": {
    "title": "...",
    "text": "...",
    "messageUrl": "https://example.com",
    "btnTitle": "View details"
  }
}
```

### Card

```json
{
  "msgtype": "card",
  "card": {}
}
```

Use the WPS card structure directly. The document notes that webhook card callbacks are not supported for interactive callback-style controls.

## Limits And Notes

- Sending limit: no more than 20 messages per minute per bot.
- Message content limit: each message should not exceed 5000 characters.
- Keep the webhook URL private.
- If the webhook uses keyword, IP allowlist, or signature protection, requests must satisfy those settings.

## Mentions

Supported mention patterns include:

- `<at user_id="12345">Name</at>`
- `<at email="somebody@wps.cn">Name</at>`
- `<at user_id="-1">Everyone</at>`

## Delivery Evidence

When reporting a send, prefer:

- target alias used
- payload type used
- HTTP status code
- short response summary

If no live webhook is available, report the send as unverified.
