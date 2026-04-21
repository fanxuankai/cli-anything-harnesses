# Media Saber Backend CLI Harness

## Target Software

- Software: Media Saber back end
- Source path: `/Users/fanxuankai/GolandProjects/media-saber-back-end`
- Stack: Go, go-zero REST services, PostgreSQL + Redis, generated route handlers

## Backend Strategy

This harness wraps the real Media Saber HTTP backend instead of reimplementing business logic.

- Runtime wrapper: `go run mediasaber.go`
- Primary transport: REST API under `/api/v1/...`
- Auth:
  - public bootstrap: `GET /api/v1/user/initAdminStatus`
  - user login: `POST /api/v1/user/login`
  - authenticated user token: raw `Authorization` header
  - authenticated apiKey: `apiKey` header

## Command Design

### session

Persistent client-side session state:

- base URL
- user token
- apiKey
- source path
- named profiles
- undo/redo for local session changes

### server

Real backend process helpers:

- `server ping`
- `server start`
- `server stop`
- `server backend-status`
- `server logs`

### auth

- `auth init-admin`
- `auth login`
- `auth whoami`
- `auth logout`
- `auth tokens`

### system

- `system status`
- `system space`
- `system basic-config`
- `system basic-config-part`
- `system task-schedule`
- `system upgrade-version`
- `system path-ls`

### downloader / directory

- `downloader list`
- `downloader detail`
- `downloader types`
- `downloader delete-qb-tags`
- `directory list`
- `directory match`
- `directory tags`
- `directory mkdir`
- `directory categories`
- `directory subcategory-options`
- `directory subcategory-list`

### site / media / api

- `site list`
- `site options`
- `site rss`
- `site rss-torrents`
- `media sources`
- `media search`
- `media search-all`
- `media autosuggest`
- `api` for generic REST calls

## State Model

The target backend is authoritative for server-side mutations. The harness keeps local state only for connection/session preferences.

- Undo/redo applies to local session state, not remote Media Saber data.
- REPL is the default in interactive terminals.
- One-shot subprocess use remains fully supported with `--json`.

## Validation Targets

- Namespace package layout: `cli_anything.mediasaber`
- Installable `setup.py`
- JSON output on every command
- Interactive REPL default path
- Unit tests plus subprocess e2e tests against a mock backend
