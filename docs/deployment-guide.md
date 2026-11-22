# Nena AI — Production Deployment Blueprint

This guide documents the fastest, most reliable, and cost-effective production deployment options for **Nena AI** (Kenyan B2G/B2B Digital Health Financing Platform).

---

## 🏆 Recommended Architecture (Zero-Cost / High Scalability Tier)

```
┌─────────────────────────────────┐
│     Global Edge CDN (Vercel)    │  <-- React 19 PWA Frontend
│   https://nena-ai.vercel.app    │      Instant static caching & offline service worker
└────────────────┬────────────────┘
                 │ HTTPS API Calls (Bearer JWT + HMAC)
                 ▼
┌─────────────────────────────────┐
│  FastAPI Cloud Service (Render) │  <-- Python 3.12/3.13 Backend
│   https://nena-api.onrender.com │      Zero-Trust 4-Stage Engine & Daraja M-Pesa Adapter
└────────────────┬────────────────┘
                 │ TLS 1.3 / PostgREST
                 ▼
┌─────────────────────────────────┐
│   Managed Database (Supabase)   │  <-- PostgreSQL 15+
│  Cape Town / Frankfurt Region   │      RLS Policies, Atomic Locks, Immutable SHA-256 Ledger
└─────────────────────────────────┘
```

---

## 🚀 Option 1: 1-Click Deployment via Render & Vercel (Recommended)

### Step 1: Deploy Database on Supabase
1. Create a free project at [supabase.com](https://supabase.com).
2. Choose **Cape Town (af-south-1)** or **Frankfurt (eu-central-1)** for regional low latency and compliance.
3. Open the **SQL Editor** in the Supabase Dashboard and run the three migration files in sequence:
   - `supabase/migrations/001_initial_schema.sql` (Creates core tables, triggers, and append-only constraints)
   - `supabase/migrations/002_rls_policies.sql` (Applies tenant isolation Row-Level Security)
   - `supabase/migrations/003_ledger_and_auth_reconciliation.sql` (Sets up atomic locks and SHA-256 integrity procedures)
4. (Optional) Run `supabase/seed.sql` to populate synthetic Kenyan clinics and vouchers.
5. In **Project Settings > API**, copy:
   - Project URL (`https://your-project.supabase.co`)
   - `anon` public key
   - `service_role` secret key

---

### Step 2: Deploy Backend API on Render or Railway
1. Push your repository to GitHub: `https://github.com/Cynthia-M-M/nena-ai`
2. Go to [render.com](https://render.com) and click **New > Web Service** (or use Blueprints with `render.yaml`).
3. Connect your GitHub repository.
4. Configure service settings:
   - **Root Directory:** `backend`
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables:
   ```env
   APP_NAME=Nena AI API
   APP_ENV=production
   CORS_ORIGINS=*
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
   APP_HMAC_SECRET=your-secure-64-character-hex-string
   MPESA_CALLBACK_SECRET=your-secure-64-character-hex-string
   MPESA_MODE=mock
   ```
6. Click **Deploy**. Your API will be live at `https://nena-ai-api.onrender.com`!
   Verify by opening `https://nena-ai-api.onrender.com/api/v1/health`.

---

### Step 3: Deploy Frontend on Vercel
1. Go to [vercel.com](https://vercel.com) and click **Add New > Project**.
2. Import your GitHub repository: `https://github.com/Cynthia-M-M/nena-ai`.
3. Configure project settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `frontend`
4. In **Environment Variables**, add:
   ```env
   VITE_API_URL=https://nena-ai-api.onrender.com
   ```
5. Click **Deploy**.
6. Your progressive web app will be globally live at `https://nena-ai.vercel.app`!

---

## 🐳 Option 2: Unified Docker VPS Deployment (DigitalOcean / AWS / Hetzner)

If you prefer hosting both frontend and backend on a single virtual server ($4 to $12/month):

1. Launch an Ubuntu 24.04 LTS instance (e.g. DigitalOcean Basic Droplet or AWS Lightsail).
2. Install Docker & Compose:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
   ```
3. Clone your repository:
   ```bash
   git clone https://github.com/Cynthia-M-M/nena-ai.git /opt/nena-ai
   cd /opt/nena-ai
   ```
4. Configure production environment in `.env`:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase keys and HMAC secrets
   ```
5. Build and launch containers:
   ```bash
   docker compose up -d --build
   ```
6. (Optional) Point your domain (`nena.health`) to your server IP and add Caddy for automatic Let's Encrypt HTTPS:
   ```Caddyfile
   nena.health {
       reverse_proxy localhost:3000
   }

   api.nena.health {
       reverse_proxy localhost:8000
   }
   ```

---

## 🔒 Production Security Checklist Before Going Live in Kenyan Clinics

- [ ] **Database RLS Enabled:** Verify `002_rls_policies.sql` is applied so clinics cannot query other clinics' records.
- [ ] **Cryptographic HMAC Key Protection:** Generate a high-entropy 256-bit secret via `openssl rand -hex 32` for `APP_HMAC_SECRET`.
- [ ] **M-Pesa Daraja Production Credentials:** When transitioning from sandbox to Safaricom Daraja live production, replace mock credentials with the registered Shortcode, Consumer Key, and Passkey.
- [ ] **Kenyan Data Protection Act (2019) Compliance:** Ensure national IDs and patient names are never logged; verify only HMAC hashes are stored in ledger events.
