# www.gregorykapfhammer.com

## Introduction

This is the Website of Gregory M. Kapfhammer that was built with Quarto.
Please review the configuration for GitHub Actions to see the steps for
building and deploying the site to Netlify.

## Commands

For deployments to Netlify, make sure to `export` the `NETLIFY_AUTH_TOKEN`
environment variable before running the following commands. This is due to the
fact that there is currently a defect in the `quarto publish` command not
retaining the authorization to publish to Netlify.

- `python scripts/publish-site.py --stage all --use-poetry-venv`
- `python scripts/publish-site.py --stage render --use-poetry-venv --render-file index.qmd`
- `python scripts/publish-site.py --use-poetry-venv --stage post-render`
- `python scripts/publish-site.py --use-poetry-venv --stage netlify`
