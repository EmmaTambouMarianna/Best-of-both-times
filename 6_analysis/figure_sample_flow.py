# Figure: sample construction flow (English). Run: python3 figure_sample_flow.py [output.png]
import sys, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib import font_manager as fm
fams = {f.name for f in fm.fontManager.ttflist}
plt.rcParams["font.family"] = "Times New Roman" if "Times New Roman" in fams else "Liberation Serif"
out = sys.argv[1] if len(sys.argv) > 1 else "figure1_sample_flow.png"

fig, ax = plt.subplots(figsize=(8.2, 8.8)); ax.set_xlim(0, 100); ax.set_ylim(9, 100); ax.axis("off")
MX, MW, H = 6, 46, 7.4          # main column x, width, box height
SX, SW = 60, 37                 # side (exclusion) column

def box(x, y, w, h, txt, bold=False, fill="white", size=10.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8",
                                fc=fill, ec="black", lw=0.9))
    ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=size,
            fontweight="bold" if bold else "normal", linespacing=1.25)

def down(y_top, y_bot):
    ax.annotate("", xy=(MX + MW / 2, y_bot), xytext=(MX + MW / 2, y_top),
                arrowprops=dict(arrowstyle="-|>", lw=0.9, color="black"))

def side(y_mid):
    ax.plot([MX + MW / 2, SX - 0.6], [y_mid, y_mid], color="black", lw=0.9)
    ax.annotate("", xy=(SX, y_mid), xytext=(SX - 3, y_mid),
                arrowprops=dict(arrowstyle="-|>", lw=0.9, color="black"))

main = [
    (90, "Forbes World's Best Management\nConsulting Firms (August 2026)\n193 firms", True),
    (76, "Founded in 2010 or earlier\n173 firms", False),
    (62, "Eligible for collection\n160 firms", False),
    (48, "Services page collected (one capture per year)\n153 firms, 2,164 firm-years", False),
    (34, "Valid firm-years\n148 firms, 1,675 firm-years", False),
    (16, "Final panel\n93 firms, 1,374 firm-years (1996–2025)", True),
]
excl = [
    (86.7, "Excluded: founded after 2010\n(n = 20 firms)"),
    (72.7, "Domain and archive verification:\n60 firms flagged, 12 corrected\nExcluded: no usable archive or site\n(n = 10); fewer than 10 archived\nyears (n = 3)"),
    (58.7, "Excluded: no services page found\n(n = 7 firms)"),
    (44.7, "Excluded firm-years:\npivot page rejected (n = 22)\nfewer than 50 words (n = 413)\nnot English or French (n = 54)"),
    (28.7, "Excluded: fewer than 10 valid years\n(n = 55 firms, 301 firm-years)"),
]
for i, (y, t, b) in enumerate(main):
    box(MX, y, MW, H, t, bold=b, fill="#EDEDED" if b else "white")
    if i < len(main) - 1:
        down(y, main[i + 1][0] + H)
for y, t in excl:
    nl = t.count("\n") + 1
    h = 1.9 * nl + 2.4
    box(SX, y - h / 2, SW, h, t, size=9.2)
    side(y)
ax.text(MX, 11, "Firm-years: annual snapshot of the services page closest to 2 July.",
        fontsize=8.8, style="italic")
plt.savefig(out, dpi=300, bbox_inches="tight"); print("saved", out)
