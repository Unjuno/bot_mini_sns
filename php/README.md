# PHP common implementation

This is the PHP port of the platform-neutral event contract. It reads one JSON
event per line and writes one JSON `OutboundReply` per line. Platform adapters
must handle authentication, webhooks, media transfer, and native message APIs.

Run:

```powershell
Get-Content event.jsonl | php bin/common-events.php
```
The normalized webhook can be served with `php -S 127.0.0.1:8081 -t bin`; POST JSON events to `/server.php`.
