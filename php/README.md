# PHP common implementation

This is the PHP port of the platform-neutral event contract. It reads one JSON
event per line and writes one JSON `OutboundReply` per line. Platform adapters
must handle authentication, webhooks, media transfer, and native message APIs.

Run:

```powershell
Get-Content event.jsonl | php bin/common-events.php
```
