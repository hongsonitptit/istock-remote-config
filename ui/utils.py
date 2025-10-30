def highlight_rows(row):
    if row.name % 2 == 0:
        # Light grey for even rows
        return ['background-color: #f0f2f6'] * len(row)
    else:
        # White for odd rows
        return ['background-color: #ffffff'] * len(row)