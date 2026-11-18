# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django 5.2.7 / Python 3.13 SG-SST (Sistema de Gestión de Seguridad y Salud en el Trabajo) system for Plastitec. Manages scheduled safety inspections (extinguishers, first-aid kits, forklifts, processes, storage areas), a physical asset registry, SVG floor-plan asset placement, and a custom role-based permission system.

`testOne` is **not** the git root — `.git` lives in the parent `Sst_betaProyect` directory.

## Commands

```bash
# Run dev server
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Django shell
python manage.py shell

# Run tests (per-app, standard Django test runner; test files currently have no real test cases)
python manage.py test
python manage.py test inspections

# System bootstrap (run in this order on a fresh DB)
python manage.py init_permissions     # roles/management/commands — creates Permission rows from PERMISSION_MATRIX
python manage.py init_roles           # roles/management/commands — creates default Role rows
python manage.py init_areas           # inspections/management/commands — seeds Area catalog
python manage.py create_datamaster    # users/management/commands — creates an initial admin user
python manage.py createsuperuser
```

There is no configured linter/formatter in the repo (no `.flake8`, `pyproject.toml`, `ruff` config, etc.) — don't assume one.

Numerous one-off scripts live in the project root (`tmp_*.py`, `clear_data.py`, `full_clear_sst.py`, `seed_*.py`, `fix_*.py`, `setup_permissions.py`, `setup_reports_perm.py`, `init_system_config.py`, `reset_sequences_sst.py`). These are ad-hoc maintenance/debug scripts from prior work, not part of the supported workflow — check what a script does before running it, and prefer the `manage.py` commands above for setup.

## Architecture

### Apps and routing (`core/urls.py`)

| URL prefix | App | Purpose |
|---|---|---|
| `/accounts/` | `users` | Auth (email-based login), user CRUD |
| `/inspections/` | `inspections` | Schedule + all 5 inspection modules + areas + reports |
| `/roles/` | `roles` | RBAC: roles, permissions, role simulation |
| `/notifications/` | `notifications` | In-app notifications |
| `/configuration/advanced/` | `system_config` | Key/value system settings, `Plano` (floor plan) catalog |
| `/configuration/` | `core.views.ConfigurationView` | General config landing page |
| `/activos/` | `gestion_activos` | Physical asset registry (extinguishers, forklifts, first-aid kits) with movement history |
| `/planos/` | `planos` | SVG floor-plan asset placement |

`core` is the Django project package (settings/urls/wsgi), not an installed app with models.

### Authentication

`users.CustomUser` (`AUTH_USER_MODEL`) extends `AbstractUser`, authenticates by **email** (`USERNAME_FIELD = 'email'`), and stores a base64 digital signature (`digital_signature`) used across inspection sign-off flows. Sessions expire after 30 minutes of inactivity (`SESSION_COOKIE_AGE = 1800`, `SESSION_SAVE_EVERY_REQUEST = True`, `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`).

### RBAC — custom, not Django's built-in permissions

This is the part most likely to trip up someone assuming Django's native `auth.Permission`/`user.has_perm` — this system ignores that entirely and implements its own:

- **`roles/models.py`**: `PERMISSION_MATRIX` is the single source of truth for which `(module, action)` pairs exist (e.g. `extinguisher: [view, create, edit, delete, details]`, `assets: [..., gestionar_movimientos]`, `planos: [view, edit]`). `Permission` rows are generated from this matrix by `init_permissions`. `Role` is a named group of `Permission`s (M2M) with `is_active`/`is_system_role` flags; `Role.has_permission(module, action)` is the actual check.
- **`users/models.py`**: `CustomUser.has_perm_custom(module, action)` is the entry point — superusers and users with role `'Administrador'` always pass; otherwise it delegates to `self.role.has_permission(...)`.
- **`roles/mixins.py`**: `RolePermissionRequiredMixin` (a CBV mixin, not a decorator) reads `permission_required = ('module', 'action')` from the view and calls `has_perm_custom`. On failure it flashes a message and redirects to `HTTP_REFERER` or `dashboard` — it does not raise 403. **Every protected CBV in the codebase sets `permission_required` this way**; when adding a new view, follow this pattern rather than Django's `PermissionRequiredMixin`.
- **`roles/templatetags/permission_tags.py`** and **`roles/context_processors.role_simulation`**: expose permission checks and simulation state to templates (e.g. for conditionally rendering sidebar/menu items).
- **`roles.middleware.RoleSimulationMiddleware`**: lets a real Administrator/superuser "simulate" another role for the current session by monkey-patching `request.user.has_perm_custom` in memory for that request only (nothing is written to the DB). Must sit after `AuthenticationMiddleware` in `MIDDLEWARE` — it already does. When debugging permission issues, check `request.session['simulated_role_id']` / `request.user._simulated_role` before assuming a DB permission problem.

### Inspections domain (`inspections/` — the largest app)

- **`Area`**: shared catalog of physical areas/zones, referenced by `InspectionSchedule`, every inspection module, and `gestion_activos.Asset`.
- **`InspectionSchedule`**: annual plan — area, inspection type (free-text matched by substring in `get_module_url`, e.g. `'extintor' in type.lower()`), frequency, scheduled date, responsible user. `generate_next_schedule()` auto-creates the next occurrence based on frequency when an inspection is completed. Status/overdue/upcoming logic is computed via properties (`is_overdue`, `is_upcoming`, `is_executable`, `status_label`, `status_css_class`), not stored — when changing inspection status values, these property branches must be updated too.
- **`BaseInspection`** (abstract model): shared fields (`inspection_date`, `area`, `inspector`, `schedule_item`, `general_status`, `observations`) for all 5 concrete modules: `ExtinguisherInspection`, `FirstAidInspection`, `ProcessInspection`, `StorageInspection`, `ForkliftInspection` (defined later in `models.py`, not shown in the excerpt above but following this base). Each has a companion `*Item`/`*CheckItem` model and (except Forklift) a `*Signature` model for digital sign-off.
- **`InspectionEvidence`**: generic-relation model (via `ContentType`) for photo evidence attached to any inspection or item.
- **`views.py` is ~2600 lines** holding CBVs (`ListView`/`CreateView`/`UpdateView`/`DetailView`) for all 5 modules plus schedule and reports — it follows a repeated per-module pattern (List/Create/Update/Detail/Sign/Report/ItemCreate/ItemUpdate). `area_views.py` was already split out from it; if extending inspection views significantly, follow that precedent and split by module (e.g. `extinguisher_views.py`) rather than growing `views.py` further.
- **`inspection_tags.py`** (templatetags): presentation helpers for inspection templates.

### Asset management (`gestion_activos/`)

Separate from the inspection checklists — this is a physical asset *registry* with lifecycle tracking:

- **`Asset`**: generic asset row (`code`, `asset_type`, `area`, optional `plano`). Has a `temporal` flag — only `True` for replacement assets created through the movement flow, never for manually created assets.
- **`ExtintorDetail` / `MontacargasDetail` / `BotiquinDetail`**: one-to-one type-specific detail tables (`OneToOneField` to `Asset`). `Asset.estado_actual` is a computed property that branches on which detail table is attached (`hasattr(self, 'extintor_detail')`, etc.) and combines stored state (`estado_movimiento` for extinguishers) with date-based logic (expiry/maintenance/review windows, with a 30-day "próximo a vencer" threshold). When adding a new asset type, add a new `*Detail` model and extend `estado_actual`/`estado_label`/`estado_css` together — they're kept in sync by hand, not derived from a shared enum.
- **`MovimientoActivo`**: append-only audit log of asset movements (`salida`, `reemplazo`, `retorno`, `baja_temporal`) — records are never deleted, this is the source of truth for `estado_movimiento` on `ExtintorDetail` and for `Asset.get_temporal_activo()`.
- Connects to `inspections.Area` (FK) and `system_config.Plano` (FK, optional) — cross-app FKs via string references (`'inspections.Area'`, `'system_config.Plano'`), so check both apps when tracing asset-to-area/plano relationships.

### `system_config/`

Generic typed key-value store (`SystemConfig.get_value(key, default)` with `config_type` in `string`/`number`/`boolean`) for editable system settings, plus the `Plano` model (named floor plans) consumed by `gestion_activos` and `planos`.

### `planos/`

Places `gestion_activos.Asset` instances as markers on an SVG floor plan (`system_config.Plano`), keeping a position history (`UbicacionActivo`). Smallest app (`views.py` ~210 lines).

## Database

Despite `requirements.txt` including `psycopg`, the active `DATABASES` config in `core/settings.py` points at a **PostgreSQL** instance (`sst_db`/`app_plas`, hardcoded host/password) — the SQLite block in that file is commented out and kept only as reference. `db.sqlite3` in the repo root is a stale leftover, not the active database. Before running the app or migrations locally, confirm a reachable Postgres instance matches those credentials, or swap in the commented SQLite block for local-only work.

## Known rough edges (don't "fix" these silently — they reflect current real state, not doc drift)

- `core/settings.py` has `DEBUG = True`, `ALLOWED_HOSTS = ['*']`, and a never-rotated default `SECRET_KEY` — fine for the current dev/intranet deployment, but flag before any change that affects production exposure.
- `InspectionSchedule.is_overdue`/`is_upcoming`/`is_executable` and `get_module_url`'s type-matching are defined twice in `models.py` (first pass then redefined further down) — the later definitions win; be aware duplicate definitions exist if searching for these properties.
