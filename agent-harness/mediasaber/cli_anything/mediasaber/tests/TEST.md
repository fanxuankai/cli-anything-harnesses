# Test Plan

## Unit

`test_core.py` covers:

- connection resolution and URL normalization
- config persistence plus undo/redo session state
- response envelope parsing, raw JSON parsing, and binary output writing
- manager endpoint mapping for auth/system/downloader/media
- dynamic command registration and representative argument mapping

These tests use mocks only and do not require a running Media Saber instance.

## End-to-End

`test_full_e2e.py` spins up a lightweight mock HTTP server and invokes the CLI through subprocess.

Validated workflows:

- public server reachability
- login and token persistence via config file
- authenticated `whoami`
- system status
- downloader listing
- cloud-storage, torrent, subscribe, message, service-ocr, pansou, hdhive smoke commands
- raw AI models/completions commands
- multipart upload command
- binary output command
- generic API passthrough
- session set / undo / redo

## Validation Commands

```bash
cd agent-harness/mediasaber
pytest cli_anything/mediasaber/tests/test_core.py -v
pytest cli_anything/mediasaber/tests/test_full_e2e.py -v
pip install -e .
cli-anything-mediasaber --help
```

## Known Limitations

- `server start` wraps the real Go backend but is not exercised in automated tests because it depends on local DB/Redis/config state.
- Undo/redo only applies to local harness session configuration.
