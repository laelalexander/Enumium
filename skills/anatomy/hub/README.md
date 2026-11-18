# Anatomy Hub

Central storage for Anatomy projects, so every PC that runs the Anatomy app sees and edits the same projects.

- **hub.js** runs on the server (no npm packages). It stores each project as plain files under
  `/var/lib/anatomy-hub/projects/<project>/`, the same layout as `C:\Anatomy\<project>`.
- **app/sync.js** runs inside the Anatomy app on each PC and keeps `C:\Anatomy` in step with the hub.

## How it behaves

- Runs still happen on the PC you start them from, because KiCad, slicers and Python need local files.
  Starting a run first pulls the latest copy and claims the project, so two PCs can't run the same
  project at once. The results upload when the run ends.
- Sync runs every 2 minutes, on Hub > Sync now, and before and after every run.
- The project list shows projects from every PC. A project made on another PC downloads the first time
  you open it, or tick "Keep a full copy of every project" to download everything.
- Per file, a change on one side wins. If both sides changed, the newer copy wins and the other is kept in
  `.anatomy/conflicts/`. The hub also keeps every overwritten or deleted file for 30 days in
  `/var/lib/anatomy-hub/trash/`.
- Not synced: per-PC environments and caches (`venv`, `.venv`, `node_modules`, `.pio`, `__pycache__`, `.git`).
  Each PC rebuilds those.
- If two PCs each made a different project with the same folder name, this PC's copy is renamed
  `<name>-<pc>` instead of being merged.

## Install on the server

As root on an Ubuntu server with nginx and certbot, from this folder:

    HUB_HOST=pyrails.com ./deploy.sh

It adds one nginx site for `HUB_HOST` (or tells you to include `snippets/anatomy-hub.conf` if a site for
that name already exists), tests it with `nginx -t`, reloads (never restarts) nginx, gets a certificate,
and prints the hub address and the access key once.

## Connect a PC

In the Anatomy app, click **Hub**, enter the hub address (`https://<host>/anatomy-hub`) and the access key,
and click Connect. Existing projects upload in the background.
