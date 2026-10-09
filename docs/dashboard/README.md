# Resource Dashboard Website

The dashboard UI is `docs/dashboard/index.html` and its generated data snapshot is `docs/dashboard/dashboard_data.json`.

Recommended GitHub Pages configuration: repository **Settings → Pages → Deploy from a branch**, branch `master`, folder `/docs`.

The **Snapshot aktualisieren** button fetches the latest published `dashboard_data.json` immediately, bypassing browser/CDN caching. The page also fetches it every three minutes and when a tab becomes visible after a long pause. This is a browser-side refresh only: it does not start a new GitHub Actions run.

The server-side **Resource Dashboard Update** workflow is scheduled every five minutes (GitHub Actions' minimum supported scheduled interval) and deploys a freshly generated snapshot to GitHub Pages after a successful run. Therefore the browser checks every three minutes, but the underlying runner/job telemetry changes only when a newer server snapshot has been successfully generated and deployed. The status line displays both the snapshot data timestamp and the browser's last successful fetch time. If the refresh fails, the last successfully displayed snapshot remains visible and the error is reported.

The **Snapshot-Workflow öffnen** link opens the Actions workflow page. Starting a server-side run there still requires the user to select **Run workflow**. The public Pages site does not embed a write token; a public static page must not contain credentials or try to bypass authenticated Actions permissions.

The dashboard is operational telemetry only. It never grants workflow permissions and never authorizes performance, promotion, orders or live trading. The layout adapts for narrow mobile screens (including Pixel 8a-sized viewports), with touch-sized controls, compact runner cards and horizontally scrollable data tables.

Android is reserve-only and excluded from the active dashboard resource pool. The manual phone workflow remains available only for bounded maintenance/diagnostics.
