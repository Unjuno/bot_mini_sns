# PHP standalone implementation

This is a standalone PHP implementation of the platform-neutral event contract.
It includes its own webhook server, persistence, platform adapters, signature
checks, media/API handling, and reply generation; it does not require Python.

Run:

```powershell
Get-Content event.jsonl | php bin/common-events.php
```
The normalized webhook can be served with `php -S 127.0.0.1:8081 -t bin`; POST JSON events to `/server.php`.
Posts are persisted in SQLite at `bin/posts.sqlite` by default. Set `PHP_DATABASE_PATH` to use another writable database path.
