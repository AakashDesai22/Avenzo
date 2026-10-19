# AVENZO — Hostinger Deployment

This directory contains deployment resources and guidance for hosting the **AVENZO Business Web Application** on Hostinger.

## Documentation
For complete step-by-step instructions on deploying the Business Web frontend to Hostinger, see:
- [Hostinger Deployment Guide](../../docs/deployment/HOSTINGER_DEPLOYMENT_GUIDE.md)
- [Monorepo Deployment Plan](../../docs/infrastructure/deployment-plan.md)

## Key Files
- `business-web/public/.htaccess`: Apache / LiteSpeed rewrite rules ensuring SPA client-side routing fallback to `/index.html` and HTTP-to-HTTPS redirection. Copied automatically into `dist/` upon build.
- `business-web/dist/`: Static output folder ready to be deployed to Hostinger's `public_html/`.
