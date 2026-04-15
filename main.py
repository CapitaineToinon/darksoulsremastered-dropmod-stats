import argparse
import csv
import json
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from stats import cache
from stats.models import (
    Category,
    CategoryListResponse,
    Game,
    GameResponse,
    Platform,
    PlatformResponse,
    Run,
    RunListResponse,
    Variable,
    VariableListResponse,
)

BASE_API = "https://www.speedrun.com/api/v1"

DSR_ID = "darksoulsremastered"
CUTOFF_DATE = date(2018, 5, 25)
PLOTS_DIR = Path("plots")


def get(path: str, params: dict[str, str] | None = None, use_cache: bool = True) -> Any:
    url = f"{BASE_API}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    if use_cache:
        cached = cache.get(url)
        if cached is not None:
            return cached
    with urllib.request.urlopen(urllib.request.Request(url)) as response:
        data = json.loads(response.read().decode())
    if use_cache:
        cache.set(url, data)
    return data


def get_game(game_id: str, use_cache: bool = True) -> Game:
    return GameResponse.model_validate(get(f"games/{game_id}", use_cache=use_cache)).data


def get_categories(game_id: str, use_cache: bool = True) -> list[Category]:
    return CategoryListResponse.model_validate(
        get(f"games/{game_id}/categories", use_cache=use_cache)
    ).data


def get_platform(platform_id: str, use_cache: bool = True) -> Platform:
    return PlatformResponse.model_validate(
        get(f"platforms/{platform_id}", use_cache=use_cache)
    ).data


def get_variables(category_id: str, use_cache: bool = True) -> list[Variable]:
    return VariableListResponse.model_validate(
        get(f"categories/{category_id}/variables", use_cache=use_cache)
    ).data


def fetch_runs(game_id: str, category_id: str, cutoff: date, use_cache: bool = True) -> list[Run]:
    runs: list[Run] = []
    offset = 0

    while True:
        response = RunListResponse.model_validate(
            get("runs", {
                "game": game_id,
                "category": category_id,
                "status": "verified",
                "orderby": "date",
                "direction": "desc",
                "max": "200",
                "offset": str(offset),
            }, use_cache=use_cache)
        )

        if not response.data:
            break

        done = False
        for run in response.data:
            if run.date is None:
                continue
            if date.fromisoformat(run.date) < cutoff:
                done = True
                break
            runs.append(run)

        if done or response.pagination.size < response.pagination.max:
            break

        offset += response.pagination.size

    return runs


def to_dropmod_label(raw: str) -> str | None:
    lower = raw.lower()
    if "no dropmod" in lower:
        return "No Dropmod"
    if "dropmod" in lower:
        return "Dropmod"
    return None


def has_dropmod_subcategory(variables: list[Variable]) -> bool:
    return any(
        to_dropmod_label(detail.label) is not None
        for var in variables
        if var.is_subcategory
        for detail in var.values.values.values()
    )


def subcategory_label(run: Run, subcategory_vars: list[Variable]) -> str | None:
    for var in subcategory_vars:
        value_id = run.values.get(var.id)
        if value_id:
            detail = var.values.values.get(value_id)
            if detail:
                label = to_dropmod_label(detail.label)
                if label is not None:
                    return label
    return None


def first_dropmod_date(all_runs: list[tuple[list[Run], list[Variable]]]) -> date | None:
    earliest: date | None = None
    for runs, subcategory_vars in all_runs:
        for run in runs:
            if run.date is None:
                continue
            if subcategory_label(run, subcategory_vars) != "Dropmod":
                continue
            d = date.fromisoformat(run.date)
            if earliest is None or d < earliest:
                earliest = d
    return earliest


def month_bins(start: date) -> list[tuple[date, date]]:
    """Return (start, end) pairs for each month from start's month to today's, oldest first."""
    today = date.today()
    bins = []
    total_start = start.year * 12 + start.month - 1
    total_end = today.year * 12 + today.month - 1
    for total in range(total_start, total_end + 1):
        year, month = total // 12, total % 12 + 1
        month_start = date(year, month, 1)
        month_end = date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)
        bins.append((month_start, month_end))
    return bins


def run_month_index(run_date: date, bins: list[tuple[date, date]]) -> int | None:
    for i, (start, end) in enumerate(bins):
        if start <= run_date <= end:
            return i
    return None


def plot_category(
    runs: list[Run],
    subcategory_vars: list[Variable],
    category_name: str,
    game_name: str,
    bins: list[tuple[date, date]],
    show: bool = False,
) -> None:
    by_subcat: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for run in runs:
        if run.date is None:
            continue
        idx = run_month_index(date.fromisoformat(run.date), bins)
        if idx is None:
            continue
        label = subcategory_label(run, subcategory_vars)
        if label is None:
            continue
        by_subcat[label][idx] += 1

    if not by_subcat:
        print(f"No runs found for {category_name}.")
        return

    _plot(by_subcat, bins, title=f"{game_name} — {category_name}", show=show)


def plot_summary(
    all_runs: list[tuple[list[Run], list[Variable]]],
    game_name: str,
    bins: list[tuple[date, date]],
    show: bool = False,
) -> None:
    by_subcat: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for runs, subcategory_vars in all_runs:
        for run in runs:
            if run.date is None:
                continue
            idx = run_month_index(date.fromisoformat(run.date), bins)
            if idx is None:
                continue
            label = subcategory_label(run, subcategory_vars)
            if label is None:
                continue
            by_subcat[label][idx] += 1

    if not by_subcat:
        return

    _plot(by_subcat, bins, title=f"{game_name} — All categories combined", show=show)


def _plot(
    by_subcat: dict[str, dict[int, int]],
    bins: list[tuple[date, date]],
    title: str,
    show: bool = False,
) -> None:
    n = len(bins)
    sorted_labels = sorted(
        by_subcat.keys(), key=lambda l: sum(by_subcat[l].values()), reverse=True
    )

    x = np.arange(n)
    x_labels = [start.strftime("%b %Y") for start, _ in bins]
    bar_width = 0.8 / len(sorted_labels)

    fig, ax = plt.subplots(figsize=(max(14, n // 3), 6))

    for i, label in enumerate(sorted_labels):
        total = sum(by_subcat[label].values())
        counts = np.array([by_subcat[label].get(m, 0) for m in range(n)])
        offsets = x - 0.4 + bar_width * (i + 0.5)
        ax.bar(offsets, counts, width=bar_width, label=f"{label} ({total})")

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Runs submitted")
    ax.set_title(title)
    ax.legend(title="Subcategory (total)", bbox_to_anchor=(1.01, 1), loc="upper left")

    PLOTS_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    path = PLOTS_DIR / f"{slug}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    if show:
        plt.show()
    else:
        plt.close()
    print(f"  Saved {path}")


def export_csv(
    all_runs: list[tuple[list[Run], list[Variable], Category]],
    platform_map: dict[str, str],
    game_name: str,
) -> None:
    slug = re.sub(r"[^a-z0-9]+", "_", game_name.lower()).strip("_")
    path = Path(f"{slug}_runs.csv")

    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "category", "date", "platform", "dropmod"])

        for runs, subcategory_vars, category in all_runs:
            for run in runs:
                platform_name = platform_map.get(run.system.platform or "", "Unknown")
                dropmod = subcategory_label(run, subcategory_vars) or ""
                writer.writerow([run.id, category.name, run.date or "", platform_name, dropmod])

    print(f"Exported {sum(len(r) for r, _, _ in all_runs)} runs to {path}")


def plot_pc_vs_console(
    all_runs: list[tuple[list[Run], list[Variable], Category]],
    platform_map: dict[str, str],
    game_name: str,
    show: bool = False,
) -> None:
    bins = month_bins(CUTOFF_DATE)

    by_platform: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for runs, _, _cat in all_runs:
        for run in runs:
            if run.date is None:
                continue
            idx = run_month_index(date.fromisoformat(run.date), bins)
            if idx is None:
                continue
            platform_name = platform_map.get(run.system.platform or "", "Unknown")
            label = "PC" if platform_name == "PC" else "Console"
            by_platform[label][idx] += 1

    if not by_platform:
        return

    _plot(by_platform, bins, title=f"{game_name} — PC vs Console", show=show)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-cache", action="store_true", help="Bypass the disk cache")
    parser.add_argument("--show", action="store_true", help="Show plots interactively in addition to saving")
    args = parser.parse_args()
    use_cache = not args.no_cache
    show = args.show

    game = get_game(DSR_ID, use_cache=use_cache)
    print(f"Game: {game.names.international}")

    platform_map = {
        pid: get_platform(pid, use_cache=use_cache).name
        for pid in game.platforms
    }

    all_categories = get_categories(game.id, use_cache=use_cache)

    # Fetch runs for every category
    all_runs: list[tuple[list[Run], list[Variable], Category]] = []
    for category in all_categories:
        print(f"Fetching runs for {category.name}…")
        variables = get_variables(category.id, use_cache=use_cache)
        subcategory_vars = [v for v in variables if v.is_subcategory]
        runs = fetch_runs(game.id, category.id, CUTOFF_DATE, use_cache=use_cache)
        print(f"  {len(runs)} runs.")
        all_runs.append((runs, subcategory_vars, category))

    # Dropmod plots only for eligible categories
    dropmod_runs = [
        (runs, subcategory_vars, category)
        for runs, subcategory_vars, category in all_runs
        if has_dropmod_subcategory(subcategory_vars)
    ]
    print(f"\nDropmod-eligible: {', '.join(c.name for _, _, c in dropmod_runs)}")

    first = first_dropmod_date([(r, v) for r, v, _ in dropmod_runs])
    if first is None:
        print("No Dropmod runs found.")
        return
    print(f"First Dropmod run: {first} — plotting from {first.strftime('%b %Y')}")

    bins = month_bins(first)

    for runs, subcategory_vars, category in dropmod_runs:
        plot_category(runs, subcategory_vars, category.name, game.names.international, bins, show=show)

    plot_summary([(r, v) for r, v, _ in dropmod_runs], game.names.international, bins, show=show)
    plot_pc_vs_console(all_runs, platform_map, game.names.international, show=show)
    export_csv(all_runs, platform_map, game.names.international)


if __name__ == "__main__":
    main()
