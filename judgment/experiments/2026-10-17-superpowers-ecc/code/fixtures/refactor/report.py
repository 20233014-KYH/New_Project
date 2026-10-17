def sales_report(rows):
    total = 0
    for r in rows:
        if r["type"] == "sale":
            total += r["amount"]
    lines = []
    lines.append("SALES")
    lines.append("-----")
    for r in rows:
        if r["type"] == "sale":
            lines.append(f'{r["name"]}: {r["amount"]:.2f}')
    lines.append(f"TOTAL: {total:.2f}")
    return "\n".join(lines)


def refund_report(rows):
    total = 0
    for r in rows:
        if r["type"] == "refund":
            total += r["amount"]
    lines = []
    lines.append("REFUNDS")
    lines.append("-------")
    for r in rows:
        if r["type"] == "refund":
            lines.append(f'{r["name"]}: {r["amount"]:.2f}')
    lines.append(f"TOTAL: {total:.2f}")
    return "\n".join(lines)
