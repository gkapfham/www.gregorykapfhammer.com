# www.gregorykapfhammer.com

## Introduction

Web site of Gregory M. using Quarto. Please review the configuration for GitHub
Actions to see the steps for building and deploying the site to Netlify.

## Commands

- `python scripts/publish-site.py --stage all --use-poetry-venv`
- `python scripts/publish-site.py --stage render --use-poetry-venv --render-file index.qmd`
- `python scripts/publish-site.py --use-poetry-venv --stage post-render`
- `python scripts/publish-site.py --use-poetry-venv --stage netlify`
