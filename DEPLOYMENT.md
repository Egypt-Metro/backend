# Deployment Guide — Metro Backend

Django 4.2 + Django REST Framework + Channels (WebSockets), served over ASGI
(uvicorn). This guide gets it running **locally** and **hosted for free, always
on**, with public API docs.

---

## Recommended free stack

| Piece | Choice | Why |
|------|--------|-----|
| Web service | **Koyeb** free instance | Free forever, **no cold starts / no sleep**, automatic HTTPS, custom domains, WebSockets supported, deploys straight from a Dockerfile in your GitHub repo. |
| Database | **Neon** free Postgres | Permanent free tier (0.5 GB), serverless, gives you a ready `DATABASE_URL`. Not auto-deleted. |
| WebSocket channel layer | **In-memory, 1 worker** | No extra service. The app uses this automatically when `REDIS_URL` is unset. Add Upstash Redis later only if you scale past one instance. |
| Static files | **WhiteNoise** | Already configured; served by the app itself, no bucket needed. |

Total cost: **$0/month**, no credit card required for Koyeb or Neon.

> Alternatives, if you prefer: **Render** free tier (simplest, but the web
> service sleeps after 15 min idle), **Fly.io** (great for WebSockets, needs a
> card), **Oracle Cloud Always Free VM** (truly unlimited, most setup — run
> `docker compose` on it). See the end of this file.

---

## 1. Run and test locally

### Option A — Docker (matches production)

```bash
cp .env.example .env
# edit .env: set SECRET_KEY and JWT_SECRET to any long random strings
docker compose up --build
```

Then, in a second terminal, create admins and seed the metro data:

```bash
docker compose exec web python manage.py reset_admin          # admin@example.com / 123
docker compose exec web python manage.py populate_metro_data  # 3 lines, 84 stations
docker compose exec web python manage.py populate_routes      # station-to-station routes
docker compose exec web python manage.py generate_test_data   # trains + cars + schedules
```

### What to open (local `:8000`, or your deployed host)

| URL | What it is |
|-----|-----------|
| `/` | Landing page / API overview |
| `/api/docs/` | **Swagger UI** — every endpoint, try-it-out. *(also `/swagger/`, `/redoc/`)* |
| `/api/schema/` | Raw OpenAPI 3 spec (import into Postman/Insomnia) |
| `/admin/` | Django admin — log in with `admin@example.com` / `123` |
| `/admin/dashboard/` | Custom admin dashboard (analytics, stations, trains, tickets, wallets, users) |
| `/health/` | Health check (JSON) |
| `/api/users/` `/api/stations/` `/api/routes/` `/api/trains/` `/api/tickets/` `/api/wallet/` `/api/analytics/` `/api/auth/` | Feature APIs |
| `wss://<host>/ws/train/<train_number>/` | Live train updates (WebSocket) |

### Option B — native (no Docker)

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # set SECRET_KEY, JWT_SECRET
# start a local Postgres however you like, point DATABASE_URL at it
python manage.py migrate
python manage.py runserver
```

### Run the test suite

Needs a Postgres reachable at `DATABASE_URL` (the settings module is
Postgres-only). Easiest:

```bash
docker run -d --name metro-pg -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=metro_test -p 5432:5432 postgres:16

ENVIRONMENT=dev DEBUG=True SECRET_KEY=x JWT_SECRET=x BASE_URL=http://localhost \
  DATABASE_URL=postgres://postgres:postgres@localhost:5432/metro_test \
  python manage.py test
```

CI runs exactly this on every push (`.github/workflows/django.yml`).

---

## 2. Create the database (Neon)

1. Sign up at <https://neon.tech> (GitHub login, no card).
2. **Create project** → pick a region near your users.
3. On the project dashboard, copy the **connection string** — it looks like:
   ```
   postgresql://USER:PASSWORD@ep-xxxx.REGION.aws.neon.tech/neondb?sslmode=require
   ```
   Keep the `?sslmode=require`. This is your `DATABASE_URL`.

---

## 3. Deploy the web service (Koyeb)

1. Push this repo to GitHub (the `Dockerfile` at the repo root is all Koyeb
   needs).
2. Sign up at <https://www.koyeb.com> (GitHub login, no card).
3. **Create Web Service → GitHub →** pick this repo/branch.
   - Builder: **Dockerfile** (auto-detected).
   - Instance: **Free**.
   - Port: **8000** (the container listens on `$PORT`, which Koyeb sets).
   - Health check path: `/health/`.
4. Add these **environment variables**:

   | Key | Value |
   |-----|-------|
   | `ENVIRONMENT` | `prod` |
   | `DEBUG` | `False` |
   | `SECRET_KEY` | a long random string |
   | `JWT_SECRET` | a different long random string |
   | `DATABASE_URL` | the Neon connection string from step 2 |
   | `BASE_URL` | `https://<your-app>.koyeb.app` (fill in after first deploy, then redeploy) |
   | `ALLOWED_HOSTS` | `<your-app>.koyeb.app` (plus any custom domain, comma-separated) |
   | `CORS_ALLOWED_ORIGINS` | your frontend origin(s), e.g. `https://myfrontend.vercel.app` |
   | `MAILGUN_API_KEY`, `MAILGUN_DOMAIN` | optional — email features degrade gracefully without them |

   Generate a secret: `python -c "import secrets; print(secrets.token_urlsafe(64))"`

5. **Deploy.** The container runs migrations + `collectstatic`, then starts
   uvicorn. First build takes a few minutes.
6. After it's live, set `BASE_URL` to the real `https://<app>.koyeb.app` URL and
   redeploy so absolute links in emails/docs are correct.

### First-run admin + data

Open a shell on the running instance (Koyeb dashboard → your service → **Console**):

```bash
python manage.py createsuperuser
python manage.py populate_metro_data     # if present
```

### Continuous deployment

Koyeb redeploys automatically on every push to the selected branch. CI
(`.github/workflows/django.yml`) runs the test suite on the same push, so keep
`main` green.

---

## 4. Custom domain (optional)

Koyeb → service → **Domains** → add `api.yourdomain.com`, then create the CNAME
it shows at your DNS provider. TLS is issued automatically. Add the domain to
`ALLOWED_HOSTS` and redeploy.

---

## 5. Public URLs

| Purpose | Path |
|---------|------|
| Swagger UI (interactive) | `/api/docs/` and `/swagger/` |
| ReDoc | `/redoc/` |
| OpenAPI schema (JSON) | `/api/schema/` and `/swagger.json` |
| Django admin | `/admin/` |
| Health check | `/health/` |
| API root examples | `/api/users/`, `/api/stations/`, `/api/routes/`, `/api/trains/`, `/api/tickets/`, `/api/wallet/`, `/api/analytics/` |
| WebSocket (live train updates) | `wss://<host>/ws/train/<train_number>/` |

Docs are public (`AllowAny`) — share `/api/docs/` directly.

---

## 6. Known limits of the free setup

- **One web worker.** Broadcasts stay within that process (fine for a single
  instance). To scale out: provision Redis (e.g. Upstash free), set `REDIS_URL`,
  and raise `WEB_CONCURRENCY` — the app switches to the Redis channel layer
  automatically and refuses `WEB_CONCURRENCY>1` without it.
- **Ephemeral filesystem.** Anything written to `MEDIA_ROOT` / `/uploads` is lost
  on redeploy. Crowd-detection images are processed transiently so this is
  usually fine; for durable uploads add object storage (e.g. Cloudinary free) and
  a `DEFAULT_FILE_STORAGE` backend.
- **External AI service.** Crowd-level endpoints call the separate `ai-metro`
  service; deploy/point that separately or those endpoints will return errors.

---

## Alternative hosts

### Render (free tier)

`render.yaml` in the repo still works on Render's **free** plan — change
`plan:` fields to `free` and drop the `redis` service (the app falls back to the
in-memory layer). Caveat: the free web service **sleeps after 15 minutes idle**
(~30–50 s cold start) and Render's own free Postgres is deleted after 30–90 days,
so still use Neon for the database.

### Fly.io

```bash
fly launch --no-deploy          # generates fly.toml from the Dockerfile
fly secrets set ENVIRONMENT=prod DEBUG=False SECRET_KEY=... JWT_SECRET=... \
  DATABASE_URL=... BASE_URL=https://<app>.fly.dev ALLOWED_HOSTS=<app>.fly.dev
fly deploy
```

No sleep, excellent WebSocket support; requires a card on file.

### Oracle Cloud Always Free VM

Provision an **Ampere (ARM) Always Free** instance, install Docker, clone the
repo, add a real `.env`, and run `docker compose up -d`. Put Caddy or nginx in
front for TLS. Truly unlimited and free, but you own the ops.
