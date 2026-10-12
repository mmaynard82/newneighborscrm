# Landing pages (development only)

CRM editors can save landing-page drafts at `/landing-pages/` once a user belongs to exactly one active workspace. They cannot publish publicly.

WordPress integration is **not enabled in the web UI**. In a staging environment only, set `NEWNEIGHBORS_WP_USERNAME` and `NEWNEIGHBORS_WP_APP_PASSWORD` (WordPress Application Password for a dedicated least-privilege editor account). Do not commit secrets.

Run `python manage.py sync_wordpress_draft <page_id>` **only with approval for the chosen staging/test page**. This creates/updates a WordPress page with `status=draft`; it does not publish. The connector is fixed to `https://newneighborsinc.com/wp-json/wp/v2/pages` to prevent arbitrary host requests.

No live lead capture has been enabled. Before production: complete tenant isolation across all apps, select real workspace for existing records, define WordPress per-workspace credentials/domain isolation, add anti-spam and verified form submission endpoints, and run the full test suite and staging integration checks.
