# Resource Dashboard Website

The dashboard UI is `docs/dashboard/index.html` and its generated data snapshot is `docs/dashboard/dashboard_data.json`.

Recommended GitHub Pages configuration: repository **Settings → Pages → Deploy from a branch**, branch `master`, folder `/docs`.

The **Update now** button opens the authenticated GitHub Actions workflow page. The daily updater also runs automatically at 03:35 UTC. No credential is embedded in the public HTML.

The dashboard is operational telemetry only. It never grants workflow permissions and never authorizes performance, promotion, orders or live trading.
