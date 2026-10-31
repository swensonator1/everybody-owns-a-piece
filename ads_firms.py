"""U.S. digital ad revenue by firm, 2025, $ billions: low and high ends (R2-22, R2-23). No firm reports U.S. ads alone.
Google high: Google advertising worldwide ($294.691B, 10-K) x Alphabet's U.S. revenue share (48%, 10-K).
Google low: Google + Meta + Amazon about 72% of U.S. digital ad spending (EMARKETER via PPC Land) x IAB's U.S. total ($294.6B),
            less Meta's low and Amazon.
Meta: low = revenue billed to U.S. customers ($74.78B, all types, 10-K); high = U.S. and Canada ad revenue by user location ($85.278B).
Amazon: EMARKETER 2026 U.S. forecast $56.71B / 1.179 growth = $48.1B (implied 2025).
TikTok: WARC via Marketing Dive, 'nearly $12 billion' of U.S. revenue at stake (2025).
Microsoft: low = Romer's own 2021 U.S. input ($6.65B); high = all of its worldwide search advertising, FY2026 ($15.176B)."""
IAB_2025 = 294.6
META_LO, META_HI = 74.78, 85.278
AMZN = 56.71 / 1.179
GOOG_HI = 294.691 * 0.48
GOOG_LO = 0.72 * IAB_2025 - META_LO - AMZN
FIRMS_LO = dict(Google=GOOG_LO, Meta=META_LO, Amazon=AMZN, TikTok=12.0, Microsoft=6.65)
FIRMS_HI = dict(Google=GOOG_HI, Meta=META_HI, Amazon=AMZN, TikTok=12.0, Microsoft=15.176)
if __name__ == '__main__':
    print(FIRMS_LO, FIRMS_HI)
