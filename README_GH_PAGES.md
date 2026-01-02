# Deploy to GitHub Pages (docs/ method)

This project is a client-only static site. To host on GitHub Pages using the `docs/` folder:

1. Build/copy site into `docs/` (script provided):

```bash
python3 deploy_to_docs.py
```

2. Commit and push to GitHub (example for `main` branch):

```bash
git add docs .nojekyll
git commit -m "Deploy site to docs/ for GitHub Pages"
git push origin main
```

3. In your repository settings on GitHub, go to Pages and set the source to "Deploy from a branch" -> `main` / `docs/` folder. Save.

4. Wait a minute and visit `https://<your-github-username>.github.io/<repo>/`.

Alternative: use a `gh-pages` branch and push the `docs/` contents there. That can be automated with a CI pipeline or the `gh-pages` npm package.

If you want, I can create a small GitHub Actions workflow to automatically deploy `docs/` on push to `main`.
