from __future__ import annotations

from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUTPUT = Path(__file__).resolve().parent / "output" / "ghoststream_figure1_methods_schematic.png"


def render() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6.5, 3.875), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    label = dict(fontfamily="DejaVu Sans", fontsize=7.7, color="#111111")
    small = dict(fontfamily="DejaVu Sans", fontsize=6.8, color="#333333")
    heading = dict(
        fontfamily="DejaVu Sans",
        fontsize=8.3,
        fontweight="bold",
        color="#111111",
    )

    ax.text(
        0.025,
        0.94,
        "A  Historical discovery and confirmation",
        ha="left",
        va="center",
        **heading,
    )
    ax.plot([0.025, 0.975], [0.515, 0.515], color="#B5B5B5", linewidth=0.55)
    ax.text(
        0.025,
        0.455,
        "B  Later blinded sensitivity analysis",
        ha="left",
        va="center",
        **heading,
    )
    ax.text(
        0.975,
        0.455,
        "begins only after the canonical set is fixed",
        ha="right",
        va="center",
        fontstyle="italic",
        **small,
    )

    x0 = 0.025
    right = 0.975
    gap = 0.027
    count = 4
    box_width = (right - x0 - gap * (count - 1)) / count
    box_height = 0.245
    xs = [x0 + i * (box_width + gap) for i in range(count)]

    def add_box(
        x: float,
        y: float,
        title: str,
        detail: str,
        *,
        fill_color: str = "white",
        edge: str = "#222222",
        dashed: bool = False,
    ) -> None:
        box = FancyBboxPatch(
            (x, y),
            box_width,
            box_height,
            boxstyle="round,pad=0.005,rounding_size=0.006",
            linewidth=0.8,
            edgecolor=edge,
            facecolor=fill_color,
            linestyle=(0, (3, 2)) if dashed else "solid",
            mutation_aspect=1,
            zorder=2,
        )
        ax.add_patch(box)
        ax.text(
            x + box_width / 2,
            y + box_height * 0.66,
            fill(title, 20),
            ha="center",
            va="center",
            fontweight="bold",
            **label,
        )
        ax.text(
            x + box_width / 2,
            y + box_height * 0.29,
            fill(detail, 27),
            ha="center",
            va="center",
            linespacing=1.15,
            **small,
        )

    def add_arrow(x_left: float, x_right: float, y: float, *, dashed: bool = False) -> None:
        ax.add_patch(
            FancyArrowPatch(
                (x_left, y),
                (x_right, y),
                arrowstyle="-|>",
                mutation_scale=8,
                linewidth=0.75,
                color="#333333",
                linestyle=(0, (3, 2)) if dashed else "solid",
                shrinkA=1,
                shrinkB=1,
                zorder=1,
            )
        )

    historical = [
        ("GMN trajectories", "quality control; Jan–Jul 2026"),
        ("Target-free scan", "fixed scaling and HDBSCAN"),
        ("Candidate frozen", "prespecified discovery gates"),
        (
            "Historical confirmation",
            "holdout and source-matched nulls; 95 canonical members",
        ),
    ]
    y_historical = 0.62
    for index, (title, detail) in enumerate(historical):
        add_box(xs[index], y_historical, title, detail)
        if index < count - 1:
            add_arrow(
                xs[index] + box_width + 0.003,
                xs[index + 1] - 0.003,
                y_historical + box_height / 2,
            )

    sensitivity = [
        ("Fixed member set", "canonical identities already defined"),
        ("Real local background", "exact candidate IDs removed"),
        (
            "Four-clique test",
            "128-event episodes and anchored quartet score",
        ),
        (
            "Targeted recovery",
            "year/bin empirical calibration; corroborative only",
        ),
    ]
    y_sensitivity = 0.105
    for index, (title, detail) in enumerate(sensitivity):
        add_box(
            xs[index],
            y_sensitivity,
            title,
            detail,
            fill_color="#F5F5F5",
            edge="#555555",
            dashed=True,
        )
        if index < count - 1:
            add_arrow(
                xs[index] + box_width + 0.003,
                xs[index + 1] - 0.003,
                y_sensitivity + box_height / 2,
                dashed=True,
            )

    ax.text(
        0.975,
        0.035,
        "The lower track is not the historical discovery method or an independent catalogue replication.",
        ha="right",
        va="center",
        fontstyle="italic",
        **small,
    )

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(OUTPUT, dpi=300, facecolor="white", edgecolor="none")
    plt.close(fig)
    return OUTPUT


if __name__ == "__main__":
    print(render())
