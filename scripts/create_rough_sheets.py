"""Create three printable A4 landscape planning sheets in reports/."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "Airtel_Dashboard_Rough_Sheets.pdf"
PAGE_W, PAGE_H = landscape(A4)
INK = colors.HexColor("#375B7A")
RED = colors.HexColor("#E4002B")
BLUE = colors.HexColor("#4C6A92")
TEAL = colors.HexColor("#188C8C")
PALE = colors.HexColor("#EFF4F7")
GRID = colors.HexColor("#E2E8EE")
DARK = colors.HexColor("#22364B")


def label(c, x, y, text, size=9, color=INK, font="Helvetica"):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, text)


def rule(c, x1, y1, x2, y2, color=INK, width=1):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)


def box(c, x, y, w, h, title, note=""):
    c.setStrokeColor(INK)
    c.setLineWidth(1.1)
    c.roundRect(x, y, w, h, 5, stroke=1, fill=0)
    label(c, x + 8, y + h - 16, title, 9, DARK, "Helvetica-Bold")
    if note:
        label(c, x + 8, y + h - 29, note, 7.2, INK)


def page_header(c, title, number, subtitle):
    label(c, 34, PAGE_H - 30, "AIRTEL TELECOM ANALYTICS  /  GROUP 3  /  DOMAIN C", 8, RED, "Helvetica-Bold")
    label(c, 34, PAGE_H - 52, title, 16, DARK, "Helvetica-Bold")
    label(c, 34, PAGE_H - 67, subtitle, 8, INK)
    label(c, PAGE_W - 96, PAGE_H - 31, number, 8, RED, "Helvetica-Bold")
    rule(c, 34, PAGE_H - 77, PAGE_W - 34, PAGE_H - 77, RED, 1.4)


def sketch_overview(c):
    page_header(
        c,
        "Overview tab | first layout draft",
        "SHEET 1 OF 3",
        "Reader: Network Capacity Planner  |  Decision: understand demand and subscriber usage",
    )
    # Laptop-screen frame and screen-fit note
    c.setStrokeColor(INK)
    c.setLineWidth(1.4)
    c.roundRect(35, 50, PAGE_W - 70, PAGE_H - 145, 8, stroke=1, fill=0)
    label(c, 50, PAGE_H - 109, "Airtel network usage | Overview", 12, DARK, "Helvetica-Bold")
    label(c, 52, PAGE_H - 124, "Understand data demand, subscriber usage patterns and capacity-planning needs.", 7.5)
    label(c, PAGE_W - 410, PAGE_H - 109, "[Connection type: All]  [Experiment group: All]", 7.5, RED, "Helvetica-Bold")
    # Exactly three metric cards
    card_y = PAGE_H - 228
    card_w = (PAGE_W - 126) / 3
    card_titles = [
        ("FIXED usage-days", "Validated count | one subscriber-date record"),
        ("FIXED T3 test", "Welch test | B > A | p-value + caveat"),
        ("Data per subscriber", "MB per usage-day and per calendar day"),
    ]
    for i, (title, note) in enumerate(card_titles):
        x = 50 + i * (card_w + 13)
        box(c, x, card_y, card_w, 70, title, note)
        label(c, x + 8, card_y + 17, "[key result]", 11, RED, "Helvetica-Bold")
    # Hero heatmap
    left_x, chart_y = 50, 91
    left_w, chart_h = 430, 220
    box(c, left_x, chart_y, left_w, chart_h, "Monthly data per subscriber by group and denominator")
    label(c, left_x + 10, chart_y + chart_h - 36, "MB per subscriber per day  |  solid row = usage-day; dashed row = calendar-day", 7)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    rows = ["A · usage-day", "A · calendar-day", "B · usage-day", "B · calendar-day"]
    gx, gy, cw, ch = left_x + 112, chart_y + 37, 44, 28
    for j, month in enumerate(months):
        label(c, gx + j * cw + 6, gy + 4 * ch + 7, month, 7)
    for i, row in enumerate(rows):
        label(c, left_x + 10, gy + (3 - i) * ch + 7, row, 7)
        for j in range(len(months)):
            shade = 0.12 + 0.10 * ((i + j) % 5)
            c.setFillColor(colors.Color(0.89, 0.18, 0.27, alpha=shade))
            c.setStrokeColor(colors.white)
            c.rect(gx + j * cw, gy + (3 - i) * ch, cw - 2, ch - 2, fill=1, stroke=1)
    # Supporting charts
    right_x, right_w = 495, PAGE_W - 545
    box(c, right_x, 247, right_w, 92, "Monthly active subscribers | treemap", "Tile size and label = active subscriber count")
    for i, month in enumerate(months):
        x = right_x + 10 + i * (right_w - 20) / 6
        w = (right_w - 22) / 6
        c.setFillColor(colors.Color(0.24, 0.45, 0.65, alpha=0.50 + i * 0.06))
        c.rect(x, 259, w, 29 + (i % 2) * 10, fill=1, stroke=0)
        label(c, x + 3, 250, month, 6, DARK)
    box(c, right_x, 91, right_w, 142, "Subscriber allowance use | violin distribution", "Per-subscriber monthly use / plan monthly allowance")
    for i in range(5):
        x = right_x + 34 + i * 44
        rule(c, x, 117, x, 174, GRID, 1)
        c.setFillColor(colors.Color(0.10, 0.55, 0.54, alpha=0.30))
        c.ellipse(x - 12 - (i % 2) * 3, 136, x + 12 + (i % 2) * 3, 158 + (i % 2) * 9, fill=1, stroke=1)
        label(c, x - 7, 124, f"P{i+1}", 7)
    label(c, 51, 61, "Global filters update all filter-sensitive charts; card count and T3 result are marked FIXED.", 7, RED)
    c.showPage()


def sketch_detail(c):
    page_header(
        c,
        "Detail tab | selected-month layout draft",
        "SHEET 2 OF 3",
        "Select one month, then inspect daily load, subscriber-level group use, and device differences",
    )
    c.setStrokeColor(INK)
    c.setLineWidth(1.4)
    c.roundRect(35, 50, PAGE_W - 70, PAGE_H - 145, 8, stroke=1, fill=0)
    label(c, 50, PAGE_H - 109, "Airtel network usage | Detail", 12, DARK, "Helvetica-Bold")
    label(c, PAGE_W - 355, PAGE_H - 109, "[Connection: All]  [Group: All]", 7.5, RED, "Helvetica-Bold")
    # Selector shares the KPI row.
    card_y = PAGE_H - 222
    box(c, 50, card_y, 103, 68, "Month", "[Jun 2025 v]")
    card_w = (PAGE_W - 230) / 3
    for i, (title, note) in enumerate([
        ("Active subscribers", "At least one usage-day"),
        ("Data carried", "Total MB / 1,024 squared = TB"),
        ("Data per usage-day", "Subscriber data / own usage-days"),
    ]):
        x = 164 + i * (card_w + 9)
        box(c, x, card_y, card_w, 68, title, note)
        label(c, x + 8, card_y + 13, "[value + unit]", 9, RED, "Helvetica-Bold")
    # Main daily calendar heatmap
    lx, ly, lw, lh = 50, 92, 430, 252
    box(c, lx, ly, lw, lh, "Daily network load | calendar heatmap")
    label(c, lx + 10, ly + lh - 34, "TB per calendar day  |  color midpoint = SQL month mean", 7)
    weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    sx, sy, cell_w, cell_h = lx + 52, ly + 26, 36, 25
    for i, day in enumerate(weekdays):
        label(c, lx + 8, sy + (6 - i) * cell_h + 7, day, 6.5)
        for j in range(7):
            shade = 0.12 + 0.10 * ((i * 2 + j) % 5)
            c.setFillColor(colors.Color(0.23, 0.42, 0.63, alpha=shade))
            c.setStrokeColor(colors.white)
            c.rect(sx + j * cell_w, sy + (6 - i) * cell_h, cell_w - 2, cell_h - 2, fill=1, stroke=1)
            label(c, sx + j * cell_w + 9, sy + (6 - i) * cell_h + 7, str(i * 4 + j + 1), 6, DARK)
    # Distribution comparison panels
    rx, rw = 495, PAGE_W - 545
    box(c, rx, 239, rw, 105, "Group A vs B | subscriber box plot", "MB per usage-day  |  n shown per group")
    # rough box and whisker lines
    for i, (name, x) in enumerate([("A", rx + 78), ("B", rx + 177)]):
        label(c, x - 5, 252, name, 8, DARK, "Helvetica-Bold")
        rule(c, x + 4, 265, x + 4, 319, BLUE if i == 0 else RED, 1.4)
        c.setStrokeColor(BLUE if i == 0 else RED)
        c.rect(x - 17, 276 + i * 4, 42, 26, fill=0, stroke=1)
        rule(c, x - 17, 289 + i * 4, x + 25, 289 + i * 4, BLUE if i == 0 else RED, 1.5)
    box(c, rx, 92, rw, 130, "Device categories | subscriber violin plot", "Smartphone and feature phone  |  counts in hover")
    for i, x in enumerate([rx + 72, rx + 175]):
        c.setFillColor(colors.Color(0.10, 0.55, 0.54, alpha=0.28))
        c.ellipse(x - 18, 122, x + 18, 177 + i * 13, fill=1, stroke=1)
        rule(c, x, 115, x, 183 + i * 13, TEAL, 1.2)
        label(c, x - 35, 105, "Smartphone" if i == 0 else "Feature phone", 7)
    label(c, 51, 61, "Month selector and global filters update all three charts and the three selected-month metric cards.", 7, RED)
    c.showPage()


def entity(c, x, y, w, h, title, fields, color=INK):
    c.setStrokeColor(color)
    c.setLineWidth(1.2)
    c.roundRect(x, y, w, h, 5, stroke=1, fill=0)
    c.setFillColor(PALE)
    c.roundRect(x, y + h - 26, w, 26, 5, stroke=0, fill=1)
    c.rect(x, y + h - 26, w, 5, stroke=0, fill=1)
    label(c, x + 8, y + h - 17, title, 9, DARK, "Helvetica-Bold")
    for i, field in enumerate(fields):
        label(c, x + 8, y + h - 43 - i * 13, field, 7.2, color)


def connector(c, points, note, note_x, note_y):
    c.setStrokeColor(RED)
    c.setLineWidth(1.15)
    path = c.beginPath()
    path.moveTo(points[0][0], points[0][1])
    for x, y in points[1:]:
        path.lineTo(x, y)
    c.drawPath(path, stroke=1, fill=0)
    x1, y1 = points[-2]
    x2, y2 = points[-1]
    c.saveState()
    c.translate(x2, y2)
    c.rotate(0 if abs(x2 - x1) > abs(y2 - y1) else (90 if y2 > y1 else -90))
    c.setFillColor(RED)
    c.wedge(-4, -4, 4, 4, 0, 360, stroke=0, fill=1)
    c.restoreState()
    label(c, note_x, note_y, note, 6.5, RED, "Helvetica-Bold")


def sketch_erd(c):
    page_header(
        c,
        "ER diagram | core network-usage model",
        "SHEET 3 OF 3",
        "Primary keys (PK), foreign keys (FK), and one-to-many joins used by the dashboard and project data",
    )
    # Base entities
    entity(c, 50, 345, 165, 145, "circles", ["PK  circle_id", "circle_name", "region"])
    entity(c, 610, 345, 180, 145, "plans", ["PK  plan_id", "plan_name", "data_quota", "plan_type", "price_inr"])
    entity(c, 333, 340, 190, 170, "customers", ["PK  customer_id", "FK  circle_id", "FK  current_plan_id", "connection_type", "ab_group", "device_type"])
    entity(c, 50, 90, 190, 150, "usage_daily", ["PK  usage_id", "FK  customer_id", "usage_date", "data_mb", "voice_minutes", "sms_count"])
    entity(c, 326, 90, 198, 150, "recharges", ["PK  recharge_id", "FK  customer_id", "FK  plan_id", "recharge_date", "amount_inr"])
    entity(c, 602, 90, 190, 150, "complaints", ["PK  complaint_id", "FK  customer_id", "complaint_date", "category", "is_resolved"])
    # Relationships are routed around the entity boxes.
    connector(c, [(215, 415), (333, 415)], "1 : N", 255, 425)
    connector(c, [(610, 415), (523, 415)], "1 : N", 548, 425)
    connector(c, [(352, 340), (280, 315), (145, 315), (145, 240)], "1 : N", 195, 323)
    connector(c, [(428, 340), (428, 240)], "1 : N", 435, 283)
    connector(c, [(505, 340), (585, 315), (697, 315), (697, 240)], "1 : N", 550, 323)
    connector(c, [(675, 345), (675, 272), (520, 272), (520, 240)], "1 : N", 548, 280)
    label(c, 47, 61, "Core dashboard joins: customers.customer_id = usage_daily.customer_id; customers.current_plan_id = plans.plan_id.", 7, RED, "Helvetica-Bold")
    label(c, 47, 47, "The source project also includes customer_features as a derived analysis table; it is not a source entity in this ER sketch.", 6.5, INK)
    c.showPage()


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=landscape(A4), pageCompression=1)
    c.setTitle("Airtel Dashboard and ER Diagram Rough Sheets")
    c.setAuthor("Class A Group 3")
    sketch_overview(c)
    sketch_detail(c)
    sketch_erd(c)
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
