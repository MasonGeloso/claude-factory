"""Camera path over the English board, authored against the dub blocks.

Framing note: the original recording showed roughly 1700 board-px of width at a
time (1280 video px at ~0.76 video-px per scene unit, against a board rendered at
1.02 px/scene-unit). Anything much tighter than that reads as absurdly zoomed in.
So views are a consistent 1700px wide -- the same "one screenful" the speaker
actually had -- and only the position changes between sections.

Motion: each section is held STATIC for its whole block, then moves to the next
section over MOVE seconds. No drift, no push. The board is dense enough that a
moving camera just makes it hard to read.
"""

VIEW_W = 1700          # board px — matches the original recording's framing
MOVE = 0.8             # seconds to travel between sections

# (x, y) top-left of the 1700px-wide view. Board is 2101x2770, so x maxes at ~400
# and y at ~1810 for a 16:9 view (956px tall).
S = {
    "hero":       (0,    0),     # JAPAN MARKET WEEK + indices + chart
    "chart":      (390,  0),     # push right onto the USD/JPY chart
    "happened":   (0,   470),    # HOW IT HAPPENED timeline
    "keepgoing":  (330, 470),    # dollar reserves -> treasuries -> FIMA
    "oneday":     (400, 430),    # ONE DAY MADE THE WEEK
    "contra":     (0,  1120),    # THE CONTRADICTION + Toyota numbers
    "tech":       (0,  1400),    # elsewhere in tech
    "nobody":     (330, 1120),   # THE NUMBER NOBODY WANTS
    "topix":      (400, 1180),   # TOPIX IS BEING CUT
    "tested":     (0,  1790),    # WE TESTED THE OBVIOUS TRADE
    "tested_res": (0,  2140),    # -0.004 / want the yen, trade the yen
    "decides":    (400, 1790),   # WHAT DECIDES THE MONTH
    "calendar":   (400, 1810),   # ON THE CALENDAR / BOJ
    "wide":       (200,  600),   # mid-board establishing view
}

BLOCK_SECTION = {
    1: "hero",        2: "hero",        3: "happened",    4: "happened",
    5: "happened",    6: "happened",    7: "happened",    8: "chart",
    9: "keepgoing",  10: "keepgoing",  11: "keepgoing",  12: "keepgoing",
    13: "contra",    14: "contra",     15: "contra",     16: "contra",
    17: "tech",      18: "tech",       19: "tech",       20: "tested",
    21: "tested",    22: "nobody",     23: "nobody",     24: "nobody",
    25: "topix",     26: "topix",      27: "topix",      28: "decides",
    29: "decides",   30: "calendar",   31: "decides",    32: "decides",
    33: "wide",      34: "wide",       35: "tested_res", 36: "hero",
    37: "hero",
}


def build_keys(blocks):
    """Hold each section static for its block, then travel to the next over MOVE."""
    keys = []
    for i, b in enumerate(blocks):
        x, y = S[BLOCK_SECTION[b["id"]]]
        nxt = BLOCK_SECTION.get(blocks[i + 1]["id"]) if i + 1 < len(blocks) else None
        keys.append((b["start"], x, y, VIEW_W))
        # hold right up to the handover, so the move happens at the seam only
        if nxt and nxt != BLOCK_SECTION[b["id"]]:
            keys.append((max(b["start"] + 0.1, b["end"] - MOVE), x, y, VIEW_W))
        else:
            keys.append((b["end"], x, y, VIEW_W))
    return sorted(keys)
