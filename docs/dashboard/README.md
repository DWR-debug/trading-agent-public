# Resource Dashboard Website

The dashboard UI is `docs/dashboard/index.html` and its generated data snapshot is `docs/dashboard/dashboard_data.json`.

Recommended GitHub Pages configuration: repository **Settings → Pages → Deploy from a branch**, branch `master`, folder `/docs`.

The **Update & deploy** button opens the authenticated GitHub Actions workflow page. That workflow generates the dashboard snapshot and deploys GitHub Pages automatically after a successful update. The public Pages site does not embed a write token. GitHub's workflow-dispatch API requires authenticated Actions write permission, so a public static page cannot safely fire the dispatch itself without introducing a credential.

The dashboard is operational telemetry only. It never grants workflow permissions and never authorizes performance, promotion, orders or live trading.


Android is reserve-only and excluded from the active dashboard resource pool. The manual phone workflow remains available only for bounded maintenance/diagnostics.
