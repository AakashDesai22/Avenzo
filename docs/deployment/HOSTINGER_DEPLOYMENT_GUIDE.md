# AVENZO Business Web — Hostinger Deployment Guide

This guide describes the end-to-end procedure for deploying the **AVENZO Business Web Application** (`React + Vite + TypeScript`) to **Hostinger** static web hosting or cloud hosting.

---

## 1. Architecture & Overview

- **Frontend Application**: React 19 Single Page Application (SPA), bundled with Vite.
- **Static Host**: Hostinger Web / Cloud Hosting (running Apache / LiteSpeed Web Server).
- **Backend API**: FastAPI backend running at `https://avenzo-cloud.teammavericks.org`.
- **SPA Routing**: Handled client-side via React Router DOM. All non-asset requests must rewrite to `/index.html` via `.htaccess`.
- **Authentication**: JWT Bearer token stored in `localStorage` (`avenzo_access_token`).

---

## 2. Pre-Deployment Build Preparation

### Step 2.1 — Verify Production API Configuration
Ensure the API base URL in `business-web/src/api/client.ts` targets the verified production backend:
- Default Production URL: `https://avenzo-cloud.teammavericks.org`
- Full API Prefix: `https://avenzo-cloud.teammavericks.org/api/v1`

### Step 2.2 — Run Verification Suite
Before building for production, run all tests and linters:

```bash
cd business-web

# Run linting
npm run lint

# Run unit and workspace test suite
npm run test
```

### Step 2.3 — Compile Production Artifacts
Execute the production build:

```bash
npm run build
```

This compiles TypeScript (`tsc -b`) and generates optimized assets into `business-web/dist/`.

### Step 2.4 — Verify `.htaccess` in Build Output
Confirm that the `.htaccess` file was copied from `business-web/public/` to `business-web/dist/`:

```bash
# Windows PowerShell
Test-Path business-web\dist\.htaccess

# Linux / macOS
test -f business-web/dist/.htaccess && echo "Found"
```

The `.htaccess` file provides:
1. `mod_rewrite` rules to route all virtual paths (e.g., `/orders`, `/inventory`, `/analytics`) to `/index.html`.
2. Cache-invalidation headers for `index.html` (prevents stale client versions).
3. Long-term caching (1 year) for hashed static chunks under `/assets/`.
4. Modern MIME types and baseline security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`).

---

## 3. Hostinger Deployment Procedure

### Method A — Hostinger File Manager (Direct Upload)

1. **Compress the Output**:
   Compress all files *inside* the `business-web/dist/` directory into a zip archive (e.g. `business-web-dist.zip`).
   > **Note:** Ensure `.htaccess`, `index.html`, and the `assets/` folder are at the root of the zip archive.

2. **Log in to Hostinger hPanel**:
   - Navigate to **Websites** -> select your target domain or subdomain (e.g. `business.teammavericks.org`).
   - Open **File Manager**.

3. **Navigate to Document Root**:
   - Open the domain's document root (typically `public_html/` or `domains/yourdomain/public_html/`).
   - If previous test files exist, back them up or delete them.

4. **Upload and Extract**:
   - Upload `business-web-dist.zip`.
   - Right-click and choose **Extract** directly into `public_html/`.
   - Verify that `.htaccess` is present and visible in the File Manager (enable "Show Hidden Files" in settings if hidden).
   - Delete the uploaded `.zip` archive.

---

### Method B — Hostinger Git Deployment / SSH (Automated / Semi-Automated)

If SSH access or Hostinger Git auto-deployment is enabled:

1. Connect to Hostinger via SSH:
   ```bash
   ssh -p <PORT> <USER>@<HOSTINGER_IP>
   ```
2. Navigate to your website's document root:
   ```bash
   cd ~/public_html
   ```
3. Deploy the compiled assets from `business-web/dist/` using `rsync` or `scp` from your build pipeline:
   ```bash
   rsync -avz --delete /path/to/Avenzo/business-web/dist/ user@hostinger_ip:~/public_html/
   ```

---

## 4. Backend CORS Configuration (Render)

Because the Business Web runs in a browser, cross-origin requests (`Fetch` / `XHR`) will trigger CORS preflight `OPTIONS` requests.

1. Once the Hostinger website domain is determined (e.g., `https://business.teammavericks.org`):
2. Log in to the **Render Dashboard**.
3. Select the `avenzo-backend` web service -> **Environment Variables**.
4. Update `ALLOWED_ORIGINS` (canonical) or `ALLOWED_ORIGINS_STR` (legacy supported) to include the production web domain:
   ```ini
   ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,https://avenzo.teammavericks.org,https://business.teammavericks.org
   ```
5. Save changes. Render will perform a zero-downtime redeploy with the updated CORS policy.

---

## 5. Post-Deployment Verification & Smoke Tests

After files are uploaded and CORS is updated:

1. **Root Access**:
   Navigate to `https://<YOUR_HOSTINGER_DOMAIN>/` in a web browser.
   - Verify it redirects to `/login` with the AVENZO branding rendered.
2. **SPA Deep Link & Refresh Test**:
   - Navigate directly to `https://<YOUR_HOSTINGER_DOMAIN>/orders`.
   - Refresh the page (`F5` or `Ctrl+R`).
   - **Expected Result:** The page loads correctly (not an Apache 404).
3. **Authentication & API Connectivity**:
   - Sign in with verified staff credentials (`ADMIN`, `BUSINESS_MANAGER`, or `STAFF`).
   - Verify that data loads on `/dashboard`, `/inventory`, `/orders`, and `/analytics`.
   - Open browser DevTools (`F12`) -> **Network** tab.
   - Confirm all requests to `https://avenzo-cloud.teammavericks.org/api/v1/*` return HTTP 200 without CORS errors.
4. **Role-Based Access Control**:
   - Verify that restricted routes (e.g. `/users` for non-admins) redirect or display permission banners as expected.

---

## 6. Troubleshooting

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| **HTTP 404 Not Found on page refresh** | Missing or inactive `.htaccess` in `public_html/` | Ensure `.htaccess` is present at the root of `public_html/` and `mod_rewrite` is enabled in Hostinger PHP/Apache settings. |
| **CORS Error (`Access-Control-Allow-Origin`)** | Web domain not registered in backend config | Add the web domain to `ALLOWED_ORIGINS` (or `ALLOWED_ORIGINS_STR`) in Render dashboard and redeploy backend. |
| **Old version keeps appearing after upload** | Browser caching `index.html` | The provided `.htaccess` disables caching for `index.html`. Perform a hard refresh (`Ctrl + Shift + R`). |
| **Mixed Content Warning** | Accessing via HTTP instead of HTTPS | Ensure Hostinger SSL is activated. The `.htaccess` will automatically enforce HTTPS redirection. |
