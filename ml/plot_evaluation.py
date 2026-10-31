"""Plot the measured historical evaluation using Matplotlib (optional dependency)."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("docs/evaluation-replay.json"))
    parser.add_argument("--out", type=Path, default=Path("docs/images/model-comparison.svg"))
    args = parser.parse_args()
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        parser.exit(1, "Install optional chart dependencies: python -m pip install -r ml/requirements-docs.txt\n")
    result = json.loads(args.input.read_text(encoding="utf-8"))
    rows = result["od"]
    fig, ax = plt.subplots(figsize=(11, 5.5), layout="constrained")
    fig.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")
    for name, label, color in (("model", "Historical trained model", "#0f766e"),
                                ("rule", "Base-wind rules", "#b45309"),
                                ("persistence", "Keep current direction", "#64748b")):
        values = [100 * row[f"{name}_acc"] for row in rows]
        intervals = [row.get(f"{name}_acc_ci_7d") for row in rows]
        lower = [value - 100 * interval[0] if interval else 0 for value, interval in zip(values, intervals)]
        upper = [100 * interval[1] - value if interval else 0 for value, interval in zip(values, intervals)]
        ax.errorbar(range(len(rows)), values, yerr=[lower, upper], label=label,
                    color=color, linewidth=2.5, marker="o", markersize=7,
                    capsize=4, elinewidth=1.2)
        for index, value in enumerate(values):
            offset = 10 if name == "model" else -18 if name == "rule" else 25 if index == 0 else 10
            ax.annotate(f"{value:.1f}%", (index, value), xytext=(4, offset),
                        textcoords="offset points", color=color, fontsize=10,
                        bbox={"facecolor": "#f8fafc", "edgecolor": "none", "pad": 0.5},
                        weight="bold" if name == "model" else "normal")
    ax.set_xticks(range(len(rows)), [f"{row['lead_h']} h" for row in rows])
    ax.set_xlabel("Forecast lead", fontsize=11)
    ax.set_ylabel("Stable-hour direction accuracy (%)", fontsize=11)
    ax.set_ylim(55, 102)
    ax.set_xlim(-0.2, len(rows) - 0.7)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#cbd5e1")
    ax.grid(axis="y", color="#e2e8f0")
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", frameon=False, fontsize=10)
    ax.set_title("Direction forecasting improves over rules at longer leads",
                 loc="left", fontsize=15, weight="bold", pad=24)
    fig.text(0.01, -0.035,
             "12 monthly folds, Nov 2025–Oct 2026 · 95% seven-day block-bootstrap intervals\n"
             "Development reviewed these test months. Trained artifacts are withheld pending data permission; the shipped demo uses rules.",
             fontsize=9, color="#475569")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, bbox_inches="tight", metadata={"Date": None})
    fig.savefig(args.out.with_suffix(".png"), bbox_inches="tight", dpi=140)
    plt.close(fig)
    print(args.out)


if __name__ == "__main__":
    main()
