"""Joe's family, 2021-2060, in 2025 dollars. Every life event is an illustration, not a forecast:
  Joe is 27 in 2021 and has worked at Walmart since 2016; his wife works part time at a company too small to be
  covered; kids are born in 2018 and 2021. Walmart automates and lays Joe off at the end of 2025 (the essay's
  "five years in"); in 2027 he's back at work for a smaller, uncovered employer at the same pay. When the parents'
  locked account reaches a 10% down payment on a starter home (Redfin, $260,508, Aug 2025; NAR's first-time-buyer
  median down payment is 10%) they buy, and the down payment becomes home equity held at its real value. Kids
  turn 18 in 2036 and 2039 and take their checks and accounts with them. Locked money earns 3% a year after
  inflation (the essay's figure)."""
import engine as E

HOUSE_PRICE = 260508.0          # R2-11 Redfin starter-home median, Aug 2025
DOWN_SHARE = 0.10               # R2-12 NAR 2025 Profile: first-time buyers' median down payment
LOCK_RETURN = 0.03
KID_BORN = (2018, 2021)
LAYOFF_END = 2025               # last year at Walmart
REHIRE = 2027                   # back at work, uncovered employer


def lock_shares(rule):
    """share of each line that is locked: (fund, ads, carbon, profit share, worker payouts)"""
    return {'half': (0.5, 0.5, 0.5, 0.5, 0.5), 'quarter': (0.25, 0.25, 0.25, 0.25, 0.25),
            'none': (0.0, 0.0, 0.0, 0.0, 0.0), 'split': (0.5, 0.5, 0.0, 0.5, 0.5)}[rule]


def family(run, carbon, ads, lock='split', joe_worker=None, burden_ratio=E.MID_COST_RATIO * (1 - E.OFFSET),
           end=2060, house=True):
    """run: engine output (the citizen fund line); carbon/ads: per-person paths (nominal to 2025, then 2025 $);
    joe_worker: dict year -> (cash to Joe from the worker trust, Joe's vested stake at year end) in nominal/2025$.
    burden_ratio: the family's carbon cost per person as a share of the GROSS fee per person. Treasury's burden is
    net of the 25% offset, so a middle person's burden is 0.571 x 0.75 = 0.43 of the gross fee per person."""
    lf, la, lc, lp, lw = lock_shares(lock)
    ps = E.joe_profit_share()
    rows = []
    parents_locked = 0.0; home_equity = 0.0; bought = None
    kid_locked = {k: 0.0 for k in KID_BORN}
    kid_at_18 = {}
    for y in range(2021, end + 1):
        dfl = E.to2025(y)
        fund_pp = run['check_pp'][y] * dfl
        ad_pp = ads['check_pp'][y] * dfl
        carb_pp = carbon['check_pp'][y] * dfl
        gross_pp = carbon['gross_pp'][y] * dfl
        kids_home = [k for k in KID_BORN if y - k < 18]
        n_home = 2 + len(kids_home)
        prof = (ps[y] * dfl) if y <= LAYOFF_END else 0.0
        wk_cash, wk_stake = (joe_worker.get(y, (0.0, 0.0)) if joe_worker else (0.0, 0.0))
        # each person's check split into spendable and locked
        per_lock = lf * fund_pp + la * ad_pp + lc * carb_pp
        per_spend = (1 - lf) * fund_pp + (1 - la) * ad_pp + (1 - lc) * carb_pp
        parents_spend = 2 * per_spend + (1 - lp) * prof + (1 - lw) * wk_cash
        parents_lock_in = 2 * per_lock + lp * prof + lw * wk_cash
        kids_spend = len(kids_home) * per_spend          # a minor's unlocked half is spent by the household
        burden = n_home * burden_ratio * gross_pp
        spendable = parents_spend + kids_spend - burden
        parents_locked = parents_locked * (1 + LOCK_RETURN) + parents_lock_in
        for k in KID_BORN:
            if y - k < 18:
                kid_locked[k] = kid_locked[k] * (1 + LOCK_RETURN) + per_lock
            elif y - k == 18 and k not in kid_at_18:
                kid_at_18[k] = kid_locked[k]
        if house and bought is None and parents_locked >= DOWN_SHARE * HOUSE_PRICE:
            bought = y
            home_equity = DOWN_SHARE * HOUSE_PRICE
            parents_locked -= DOWN_SHARE * HOUSE_PRICE
        building = parents_locked + home_equity + wk_stake
        rows.append(dict(year=y, kids_home=len(kids_home), checks_household=n_home * (fund_pp + ad_pp + carb_pp),
                         fund_pp=fund_pp, ad_pp=ad_pp, carbon_pp=carb_pp, profit_share=prof, worker_cash=wk_cash,
                         carbon_cost=burden, spendable=spendable, parents_locked=parents_locked,
                         home_equity=home_equity, worker_stake=wk_stake, building=building,
                         kid_accounts=sum(kid_locked[k] for k in kids_home)))
    return dict(rows=rows, bought=bought, kid_at_18=kid_at_18)


def joe_worker_track(run, d):
    """Joe's slice of the worker side while he works at Walmart (2021-2025), and what happens at the layoff.
    Company trusts: equal per Walmart worker (new shares plus recycled shares), diluted by later issues, valued at
    Walmart's value after the trim. Pooled designs (E, G): equal per covered worker across all companies.
    Cash to Joe while employed: his share of the trust's cash not needed for leavers (the engine's pass ratio).
    Returns year -> (cash to Joe this year, Joe's stake at year end), both in 2025 dollars."""
    if d.worker == 'F':
        return {}
    pooled = d.worker in ('E', 'G')
    b = 0 if pooled else E.WMT_BUCKET
    u = 0.0
    out = {}
    for y in range(2021, 2026):
        dfl = E.to2025(y)
        i = run['issue'][y]
        u *= (1 - i)
        give = run['alloc_pw'][y][b]
        pr = run['pass_ratio'][y][b]
        if pooled:
            u += give / E.EMPLOYEES_SPX                      # fraction of all covered companies
            stake = u * run['Vend'][y] * 1e9
            cash = u * run['payouts'][y] * 1e9 * pr
        else:
            u += give / E.WMT['emp'][y]                      # fraction of Walmart
            stake = u * E.WMT['mv'][y] * (1 - run['trim'][y]) * 1e9
            cash = u * E.WMT['cash'][y] * (1 - run['trim'][y]) * 1e9 * pr
        out[y] = (cash * dfl, stake * dfl)
    stake25 = out[2025][1]
    tenure_at_layoff = 2025 - 2016 + 1
    vested = stake25 if tenure_at_layoff >= d.vesting else 0.0
    if d.worker in ('D', 'E', 'C'):
        out[2026] = (vested, 0.0)                            # paid out in cash
    elif d.worker in ('A_hold', 'A_forever'):
        yld = E.WMT['cash'][2025] / E.WMT['mv'][2025]        # Walmart's 2025 cash yield, 1.76%
        for y in range(2026, 2061):
            out[y] = (vested * yld, vested)                  # he keeps the shares (illustration: never sells)
    elif d.worker == 'B':
        wait = int(max(run['max_wait'].values()))
        pay_y = 2026 + max(0, wait - 1)
        for y in range(2026, 2061):
            out[y] = (vested if y == pay_y else 0.0, vested if y < pay_y else 0.0)
    return out
