# Deploying to Vercel

Live app: <https://analog-earth.vercel.app>

The full API needs about 700 MB of NetCDF and a Python scientific stack, which does not fit a Vercel function. The globe only calls a fixed set of endpoints, so those responses are exported once as static files and served from a public **Vercel Blob** store (`analog-earth-data`); `frontend/` is deployed as a static site.

```bash
./deploy/deploy.sh
```

It (1) runs `python -m backend.api.export_static` into `deploy/static/` (git-ignored, 5 MB), (2) uploads each file to Blob, (3) writes the Blob URL into `frontend/js/config.js`, (4) runs `vercel deploy --prod` from `frontend/`.

One-time setup: `npx vercel login`; in `frontend/` run `npx vercel link --project analog-earth` and `npx vercel blob create-store analog-earth-data --access public --yes`. This writes `frontend/.env.local` with the Blob token (git-ignored).

Limits: the hosted copy serves only the precomputed presets (no custom weights, no arbitrary-point `/site` query; the app does not use them). Rerun the script after any `make scores`.
