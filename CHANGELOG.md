# Changelog

All notable changes to BuilderOS are documented here.

## [2.0.0] — 2026-08-18

First tagged release. Development happened locally before version control was set up properly, so this release combines what would normally be two versions (CLI tool, then web dashboard) into one starting point.

### Added
- **Project registry** — track local projects in a JSON file (`projects.json`), each with a name, path, GitHub URL, and status.
- **Git status reading** — parses `git status --porcelain --branch` to report modified files, untracked files, current branch, and ahead/behind counts relative to the remote.
- **Commit automation** — stage and commit changes with a confirmation prompt before anything is written.
- **Push automation** — pushes to GitHub, automatically detecting and fixing missing upstream tracking branches.
- **GitHub repo creation** — create a new GitHub repository directly from BuilderOS via the GitHub REST API, then clone it locally and register it, all in one flow.
- **Registry management** — add, remove, and update the status (`not started` / `in progress` / `done`) of tracked projects.
- **Project selection menu** — check on a single project and stay in an interactive loop (refresh, commit, push) until quitting back to the main menu.
- **Web dashboard** (Flask) — a local browser-based view of all tracked projects showing live git status, with separate Commit and Push actions per project (Push only appears once there's something committed locally waiting to go up), matching the CLI's deliberate two-step confirmation style.
- **Error handling** — graceful handling of duplicate repo names, network failures (timeouts, no connection), and clone failures, replacing raw stack traces with clear messages.

### Notes
- Secrets (GitHub personal access token) are stored in a local `.env` file, excluded from version control via `.gitignore`.
- No multi-user or hosted deployment — this is a single-user, local-only tool by design.