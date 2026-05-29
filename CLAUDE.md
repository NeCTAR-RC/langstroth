# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Langstroth is the Django-based status page for the NeCTAR Research Cloud. It surfaces outage information, allocations data, infrastructure composition visualisations, and user/usage statistics drawn from Nagios, Graphite, and the NeCTAR allocations API.

## Commands

Tests and linting run through `tox`:

- `tox` — run the default envlist (`py312`, `pep8`, `jshint`).
- `tox -e py312` — Django unit tests via `django-admin test --settings=langstroth.settings_test --exclude-tag selenium` (Python 3.12; use this env to run the unit tests). Extra args pass through as `{posargs}` (e.g. `tox -e py312 -- langstroth.outages.tests.test_foo.SomeTest.test_bar`).
- `tox -e pep8` — runs `pre-commit run --all-files` (ruff, ruff-format, hacking/flake8-import-order, doc8, plus the standard hygiene hooks).
- `tox -e cover` — coverage run + HTML/XML report; fails under 90%.
- `tox -e jshint` / `tox -e jscs` — JS lint/style; installs node via `nodeenv`.
- `tox -e selenium` — separate env that uses `langstroth.settings_selenium` and the `selenium` tag (excluded from the default test run).

Selenium tests are tagged and excluded from the default env — do not assume `tox` exercises them.

Running the dev app (from README):

```
./manage.py migrate
./manage.py runserver
```

Container build is via `make build` / `make push` (uses `docker/Dockerfile`, tag derived from `git describe`).

## Settings layering

`langstroth/settings.py` imports `defaults.py` then `exec`s `/etc/langstroth/settings.py` if it exists — production overrides live outside the repo. There are three other settings modules selected via `--settings=`:

- `settings_test` — used by `tox -e py312` and `tox -e cover`. SQLite, dummy Nagios/Graphite URLs.
- `settings_selenium` — used by `tox -e selenium`.
- `settings_example` — reference template, not imported.

When adding configuration, put the default in `defaults.py` so production overrides via `/etc/langstroth/settings.py` continue to work; do not put environment-specific values in `settings.py` itself.

## Architecture

Single Django project (`langstroth/`) with three feature apps plus the project-level views:

- `langstroth/` (project root) — `views.py` serves the home/composition/growth pages and proxies to `graphite.py` (Graphite queries) and `nagios.py` (availability/status scraping). `models.py` defines a custom `User` (`AbstractUser` + `sub` UUIDField for OIDC). `auth.py` holds `NectarAuthBackend` (extends `mozilla_django_oidc`) and the `NoDjangoAdminForEndUserMiddleware` that bounces non-staff users away from `/admin/`.
- `langstroth/outages/` — outage tracking with `Outage` + `OutageUpdate` models. Read the comment at the top of `outages/models.py` for the two intended workflows (scheduled vs. unscheduled) and the state machine; the `is_current`, `start`, `end`, and `status_display` properties on `Outage` derive from the latest `OutageUpdate` rather than fields on the outage itself. Exposed via DRF (`outages/api.py` registered under `/api/v1/outages/`) and a server-rendered UI (`outages/urls.py`).
- `langstroth/nectar_allocations/` — read-only browser over the external NeCTAR allocations REST API (`ALLOCATION_API_URL`). The `FOR_CODE_SERIES`/`FOR_CODE_RANGES` settings control which ANZSRC Field-of-Research code set is requested.
- `langstroth/user_statistics/` — Graphite-backed user growth views; `USER_STATISTICS_START_DATE` anchors the time series.

Authentication has two modes selected by `USE_OIDC` in settings — the URL patterns in `langstroth/urls.py` swap between OIDC and the classic Django login view at startup. When `USE_OIDC=True`, `NectarAuthBackend._assign_user_roles` maps the `roles` claim to `is_staff` / `is_superuser` and adds staff to the "outage managers" group created by migration `outages/0002_make_outage_manager_group.py` — permissions for what staff can edit live on that group, not in code.

Static assets are compiled by `django_compressor` + `django-libsass` (SCSS in `static/scss/`) and served by `whitenoise` (`CompressedManifestStaticFilesStorage`). `COMPRESS_ENABLED`/`COMPRESS_OFFLINE` track `not DEBUG`, so production needs `collectstatic` + `compress`.

Health-check endpoints (`/healthcheck/startup-probe/`, `/healthcheck/liveness-probe/`) are wired in `urls.py` for container orchestration.

## Style

- Ruff is the formatter and primary linter (`line-length = 79`, `quote-style = "preserve"`). `tox -e pep8` is the gate.
- Imports follow `flake8-import-order` pep8 style with `application-import-names = langstroth` (enforced via openstack/hacking in pre-commit).
- `setup.cfg`/`setup.py` use `pbr`; versioning is derived from git tags.

## Project conventions

- Conventional commits.
- Always sign commits with `git commit -s`.
