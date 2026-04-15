# src-categories-stats

Fetches all verified speedrun submissions for **Dark Souls Remastered** from the [speedrun.com API](https://www.speedrun.com/api) and plots monthly run counts per category, broken down by **Dropmod vs No Dropmod**.

## What it does

- Fetches every verified run for each eligible category (those with a Dropmod/No Dropmod subcategory) going back to the game's release on 2018-05-25
- Plots start from the month of the very first Dropmod run, so the charts aren't padded with empty space
- Produces one bar chart per category and a final combined chart across all categories
- Saves all plots as PNG files in the `plots/` directory
- Caches all API responses to disk for one hour to avoid redundant requests; bypass with `--no-cache`

## Usage

```bash
uv run python main.py
uv run python main.py --no-cache
```

## Requirements

- Python 3.14+
- [uv](https://github.com/astral-sh/uv)

Dependencies are managed by uv and defined in `pyproject.toml`. Run `uv sync` to install them.

## Project structure

```
main.py               # Entry point
stats/
  models/
    game.py           # Pydantic models for the /games endpoint
    category.py       # Pydantic models for the /categories endpoint
    run.py            # Pydantic models for the /runs endpoint
    variable.py       # Pydantic models for the /variables endpoint
  cache.py            # Disk cache with 1-hour TTL
plots/                # Generated PNG files (git-ignored)
.cache/               # API response cache (git-ignored)
```

## Credits

Built with [Claude Code](https://claude.ai/code) by Anthropic.
