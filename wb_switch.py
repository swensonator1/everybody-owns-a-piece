"""Workbook: Switches and Scenarios tabs."""
from build_wb_part1 import *
import engine as E
import scenarios as S
from wb_data import DR, HIST_ROW

SW = {}          # Switches: key -> absolute ref
SCEN_NAMES = ['Central (no real growth, 2025 cash yield)', 'Mature fund into 2000-2002', 'Mature fund into 2008-2009',
              'Falling profits and buybacks, heavy worker withdrawals',
              'AI boom: profits up, jobs down, cash to data centers', 'Prices fall back to average valuation',
              'Mature fund into 2000-2002 (half of buybacks offset by stock pay)',
              'Mature fund into 2008-2009 (half of buybacks offset by stock pay)', 'Cash squeeze without the boom',
              'Average valuation, then 2008-2009']
SCEN_DESC = ['No real growth in company value; companies keep paying 2.70% of their value in cash each year',
             "The fund is full by 2040; in 2046 it meets 2000-2005's real price and payout changes",
             "The fund is full by 2040; in 2046 it meets 2008-2013's real price and payout changes",
             'Illustrative: values fall 35% and payouts 30% two years running while layoffs add 10 points to separations',
             'BlackRock AI case (13.2% real a year to 2035); cash paid out falls to 1.5% while companies build; covered jobs fall 3% a year',
             'Valuations fall from a CAPE of 39.6 to 17.4 over 2026-2035 while cash paid stays the same in real terms',
             'As the 2000 replay, but half of buybacks are offset by stock pay (Liang and Sharpe)',
             'As the 2008 replay, but half of buybacks are offset by stock pay',
             'Cash paid out falls to 1.5% for eight years and values do not rise',
             'Valuations fall back to average, then 2008-2013 hits in 2046']
AD_OPTIONS = ['Targeted ads, 80% counted (round one)', 'Targeted ads, search left out', 'Romer default schedule',
              'Romer alternative schedule', 'Flat 30% above $5 billion', '0/20/35% steps']
LOCKS = ['split', 'half', 'quarter', 'none']
PRESETS = ['Winning setup', 'Essay as written', 'Round one bookkeeping', 'Custom']
WORKER_CODES = ['F', 'G', 'A_forever', 'A_hold', 'B', 'C', 'D', 'E']


def dv_list(ws, cell, items=None, rng=None):
    if items is not None:
        dv = DataValidation(type='list', formula1='"' + ','.join(items) + '"', allow_blank=False)
    else:
        dv = DataValidation(type='list', formula1=rng, allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(cell)


def build_switches(B):
    ws = B.wb['Switches']
    put(ws, 'A1', 'Switches', 'title')
    put(ws, 'A2', 'Every open choice is a cell on this tab. Pick a setup in C4, or pick Custom and change the yellow cells in column G. '
                  'Everything else (Model, Joe 40 years, Who paid, Government, Day one, Stress tests) recalculates.', 'note')
    put(ws, 'B4', 'Setup in use', bold=True)
    put(ws, 'C4', 'Winning setup', 'in', fill=YELLOW, bold=True)
    dv_list(ws, 'C4', PRESETS)
    SW['preset'] = B.name('preset', ws, 'C4')
    put(ws, 'D4', 'Colors: blue = typed-in value; black = calculated; green = pulled from another tab; yellow = a switch you can change.', 'note')
    hdr = ['Setting', 'Unit', 'In use'] + PRESETS[:3] + ['Custom', 'Allowed values and what they mean']
    for c, h in zip('ABCDEFGH', hdr):
        put(ws, f'{c}7', h, 'h')
    rows = [
        ('worker', "What happens to a worker's shares when they leave", 'code', 'F', 'D', 'D', 'F',
         'F = whole quarter to the citizen fund (no worker trust); G = pooled worker fund pays income only, leavers keep nothing; '
         'A_forever = leavers keep their shares and they count toward the quarter for good; A_hold = they keep them, counted while held, 20% sold a year; '
         'B = trust buys leavers out from its own cash only (they wait); C = the company pays leavers cash; '
         'D = trust pays leavers, then tops up with new shares; E = D with a portable account across covered companies', WORKER_CODES),
        ('alpha', 'Worker trust share of the new shares', 'share', 0.5, 0.5, 0.5, 0.5, 'Ignored when the code is F. 0.2 = the "small worker trust" test.', None),
        ('vesting', 'Vesting cliff', 'years', 0, 0, 0, 0, '0 = vested at once; 3 = the federal cliff limit (26 U.S.C. 411). Forfeits go back to the people still there.', None),
        ('turnover', 'People who leave or retire', 'scale', 1, 1, 0, 1, '1 = real turnover (fitted to BLS tenure); 0 = nobody ever leaves (round one, the essay as written).', None),
        ('retention', 'E only: share of leavers who land at another covered company', 'share', 0.10, 0.10, 0.10, 0.10, '0.10 = companies of 5,000+ (S&P 500); 0.30 = all firms above the size line (Census J2J, R2-15).', None),
        ('sale_rate', 'A only: share of former workers\' shares sold each year', 'share', 0.20, 0.20, 0.20, 0.20, 'Behavior, not measured. Matters only for A_hold.', None),
        ('payout_rate', 'Citizen fund payout: rate', 'share', 0.80, 0.03, 0.03, 0.80, 'Applied to the base below. P10 = 80% of five-year average cash; P1 = 3% of Jan 1 value.', None),
        ('payout_base', 'Citizen fund payout: base', 'code', 'cash_avg5', 'jan1', 'jan1', 'cash_avg5',
         "jan1 = fund's value on Jan 1; avg5 = fund's stake x five-year average company value; cash_avg5 = fund's stake x five-year average cash companies paid owners (after the trim, real).", ['jan1', 'avg5', 'cash_avg5']),
        ('cash_cap', 'Citizen fund payout: limit', 'code', 'cash_res', 'none', 'none', 'cash_res',
         'none = pay the rule even if it means selling shares; cash = never more than cash in; cash_res = never more than cash in plus the reserve.', ['none', 'cash', 'cash_res']),
        ('cap_on', 'Pay out the reserve above its cap?', 'Yes/No', 'Yes', 'Yes', 'No', 'Yes', 'No = the reserve just grows (round one).', ['Yes', 'No']),
        ('cap_years', 'Reserve cap', 'years of checks', 2, 2, 2, 2, 'Above this the extra is paid out as a bonus.', None),
        ('spread', 'Share of the reserve above its cap paid out each year', 'share', 0.2, 1.0, 1.0, 0.2, '0.2 = a fifth a year (smooths the bonus); 1 = all at once.', None),
        ('issue_rate', 'New shares each year', 'share of company', 0.015, 0.015, 0.015, 0.015, "The essay's 1.5%.", None),
        ('target', 'Combined target for the trusts', 'share of company', 0.25, 0.25, 0.25, 0.25, "The essay's quarter.", None),
        ('us_share', 'Foreign formula: U.S. share of revenue', 'share', 1.0, 1.0, 1.0, 1.0, '1 = no adjustment. 0.71 = S&P DJI\'s 2025 U.S. share (S51); 0.57 = the low end. Issue and target both scale by it.', None),
        ('coverage', 'Covered companies', 'code', 'S&P 500', 'S&P 500', 'S&P 500', 'S&P 500', 'S&P 500 or All U.S.-listed. Private companies are not modeled (no public value data).', ['S&P 500', 'All U.S.-listed']),
        ('pay_offset', 'Share of the profit share that comes back out of base pay', 'share', 0.0, 0.0, 0.0, 0.0, 'France: about 0 for most workers, about 1 for high-skill (R2-18). Phases in over five years.', None),
        ('fund_cost', 'Citizen fund running cost', 'of value a year', 0.0005, 0.0005, 0.0005, 0.0005, 'About what large index funds charge; 0.2% = the earlier model (S50).', None),
        ('haircut', 'Coverage test: net buybacks lower in 2021-2025 by', 'share', 0.0, 0.0, 0.0, 0.0, '0.10 = the reviewers\' test.', None),
    ]
    r = 8
    for key, lab, unit, a, b, c, d, note, lst in rows:
        put(ws, f'A{r}', lab); put(ws, f'B{r}', unit)
        fmt = FMT_P if unit in ('share', 'share of company') else ('0.00%' if key == 'fund_cost' else None)
        put(ws, f'C{r}', f'=INDEX(D{r}:G{r},MATCH($C$4,$D$7:$G$7,0))', fmt=fmt, bold=True)
        for col, v in zip('DEF', (a, b, c)):
            put(ws, f'{col}{r}', v, 'in', fmt=fmt)
        put(ws, f'G{r}', d, 'in', fmt=fmt, fill=YELLOW)
        if lst:
            dv_list(ws, f'G{r}', lst)
        put(ws, f'H{r}', note, 'note', wrap=False)
        SW[key] = B.name(key, ws, f'C{r}')
        r += 1
    # ---------------- other switches
    r += 1
    put(ws, f'A{r}', 'Other switches (not part of the three setups)', 'h'); r += 1
    put(ws, f'A{r}', 'Setting', 'h'); put(ws, f'B{r}', 'Unit', 'h'); put(ws, f'C{r}', 'Value', 'h'); put(ws, f'H{r}', 'Allowed values and what they mean', 'h'); r += 1
    # list ranges for long dropdowns live in column K
    lst0 = 8
    for i, nm in enumerate(SCEN_NAMES):
        put(ws, f'K{lst0 + i}', nm, 'note')
    for i, nm in enumerate(AD_OPTIONS):
        put(ws, f'L{lst0 + i}', nm, 'note')
    put(ws, 'K7', 'List: scenarios', 'note'); put(ws, 'L7', 'List: ad levy bases', 'note')
    other = [
        ('scenario', 'Path for the market (stress test)', 'name', SCEN_NAMES[0], 'Pick one of the ten paths (column K). The Stress tests tab scores the path picked here.', f'=$K${lst0}:$K${lst0 + 9}', None),
        ('carbon_on', 'Carbon fee in the plan?', 'Yes/No', 'Yes', 'No = no fee, no rebate, no higher prices (the floor without carbon).', None, ['Yes', 'No']),
        ('rebate', 'Share of the carbon fee sent back as checks', 'share', 1.0, '1 = all of it (the essay); 0.75 = keep a quarter to cover the 25% offset (the carbon line breaks even; the plan\'s other budget lines still have their own net cost).', None, None),
        ('decline', 'Emissions decline per year after 2025, with the fee', 'per year', 0.025, '2.5% = what RFF\'s with-fee path did in 2021-2025 (S15); 7.5% = the fast-decarbonization test (the 2035 NDC pace, R2-27).', None, None),
        ('ad_base', 'Ad levy base', 'name', AD_OPTIONS[0], 'See the Ad levy tab. Romer and flat options use firm-level U.S. ad revenue ranges for 2025. The winning base is Flat 30% above $5 billion (about $201 a person at the middle); the default stays on round one\'s $197 line so the totals match the report and the pass-line runs.', f'=$L${lst0}:$L${lst0 + 5}', None),
        ('ad_point', 'Where in the firm revenue range', 'Low/Middle/High', 'Middle', 'Only for the four firm-based options.', None, ['Low', 'Middle', 'High']),
        ('ad_shrink', 'Ad levy after 2025 as a share of its 2025 size (per person)', 'share', 1.0, '1 = held at 2025 (round one); 0.75 = the smaller-ad-base test.', None, None),
        ('lock', "Lock rule for Joe's family", 'name', 'split', 'split = carbon checks fully spendable, half of everything else locked; half = half of every check (the essay); quarter; none.', None, LOCKS),
        ('lock_return', 'Locked account return after inflation', 'per year', 0.03, "The essay's 3%.", None, None),
        ('spread_d1', 'Day-one test: discount spread', 'per year', 0.0, '0 = use the 2025 cash yield (2.70%); try 3.5%, 4%, 5%.', None, None),
    ]
    for key, lab, unit, v, note, rng, lst in other:
        put(ws, f'A{r}', lab); put(ws, f'B{r}', unit)
        fmt = FMT_P if unit in ('share', 'per year') else None
        put(ws, f'C{r}', v, 'in', fmt=fmt, fill=YELLOW, bold=True)
        if rng:
            dv_list(ws, f'C{r}', rng=rng)
        elif lst:
            dv_list(ws, f'C{r}', lst)
        put(ws, f'H{r}', note, 'note')
        SW[key] = B.name(key, ws, f'C{r}')
        r += 1
    # ---------------- plan constants
    r += 1
    put(ws, f'A{r}', "The essay's other rules and fixed assumptions (blue = typed in; change with care)", 'h'); r += 1
    consts = [
        ('ps_rate', 'Profit share', 'of pre-tax profit', 0.10, 'Essay p.4.'),
        ('ps_cap', 'Profit share cap', "of each worker's pay", 0.25, 'Essay: three months\' pay.'),
        ('trim', 'What the profit share takes out of company values and payouts', 'share', 0.09, 'Round one: 10% of after-tax profit before the cap, a little less with it.'),
        ('fee21', 'Carbon fee in 2021', '$ per ton', 43, 'Baker-Shultz path (S14).'),
        ('climb', 'Carbon fee climb above inflation', 'per year', 0.05, 'S14.'),
        ('collect', 'Cost of collecting the carbon fee', 'of the fee', 0.01, 'Earlier model (S50).'),
        ('ad_rate', 'Ad levy rate (round-one base)', 'of targeted ad revenue', 0.30, 'Essay p.9.'),
        ('ad_targeted', 'Share of internet ads counted as targeted', 'share', 0.80, 'Earlier model (S50); nobody measures it.'),
        ('ad_collected', 'Share of the ad levy actually collected', 'share', 0.95, 'Earlier model (S50).'),
        ('joe_pay', "Joe's yearly pay", '$', 45000, 'Essay.'),
        ('pg1', 'Population growth a year through 2036', 'per year', 0.003, 'CBO (S38).'),
        ('pg2', 'Population growth a year after 2036', 'per year', 0.001, 'CBO (S38).'),
        ('house', 'Starter-home price', '$', 260508, 'Redfin, Aug 2025 (R2-11).'),
        ('down', 'Down payment', 'share of price', 0.10, "NAR first-time buyers' median (R2-12)."),
        ('kid1', 'First child born', 'year', 2018, 'Illustration.'),
        ('kid2', 'Second child born', 'year', 2021, 'Illustration.'),
    ]
    for key, lab, unit, v, note in consts:
        put(ws, f'A{r}', lab); put(ws, f'B{r}', unit)
        fmt = FMT_P if unit in ('share', 'per year', 'of pre-tax profit', "of each worker's pay", 'of the fee',
                                'of targeted ad revenue', 'share of price') else ('#,##0' if unit == '$' else None)
        put(ws, f'C{r}', v, 'in', fmt=fmt)
        put(ws, f'H{r}', note, 'note')
        SW[key] = B.name(key, ws, f'C{r}')
        r += 1
    # ---------------- pass lines
    r += 1
    put(ws, f'A{r}', 'Pass lines (set before any run; each one is a value choice)', 'h'); r += 1
    passes = [
        ('pl_fund', 'Largest one-year fall in the ownership dividend, after inflation', 'share', 0.15),
        ('pl_whole', 'Largest one-year fall in the whole check (dividend, ads, carbon)', 'share', 0.10),
        ('pl_leg30', "2020 owners' share of the companies in year 30 (2050), at least", 'share', 0.73),
        ('pl_leg100', "2020 owners' share in year 100 (2120), at least", 'share', 0.70),
        ('pl_issue', 'Most new shares in any stress year once the trusts are full', 'share of company', 0.005),
        ('pl_wait', 'Longest wait for a leaver to be paid in full', 'years', 6),
    ]
    for key, lab, unit, v in passes:
        put(ws, f'A{r}', lab); put(ws, f'B{r}', unit)
        put(ws, f'C{r}', v, 'in', fmt=(FMT_P if unit.startswith('share') else None), fill=YELLOW)
        SW[key] = B.name(key, ws, f'C{r}')
        r += 1
    put(ws, f'A{r}', 'Minimum reserve: zero. The fund may spend its reserve to nothing but never sells shares to pay checks (counted on Stress tests).', 'note'); r += 2
    # ---------------- derived flags
    put(ws, f'A{r}', 'Derived (calculated from the cells above; used by the Model)', 'h'); r += 1
    w = SW['worker']
    derived = [
        ('tgt', 'Target, after the foreign formula', f"={SW['target']}*{SW['us_share']}", FMT_P2),
        ('rate', 'New shares a year, after the foreign formula', f"={SW['issue_rate']}*{SW['us_share']}", FMT_P2),
        ('alpha_eff', 'Worker share of new shares in use', f"=IF({w}=\"F\",0,{SW['alpha']})", FMT_P),
        ('isF', 'Code is F', f'=IF({w}="F",1,0)', '0'), ('isG', 'Code is G', f'=IF({w}="G",1,0)', '0'),
        ('isAf', 'Code is A_forever', f'=IF({w}="A_forever",1,0)', '0'), ('isAh', 'Code is A_hold', f'=IF({w}="A_hold",1,0)', '0'),
        ('isB', 'Code is B', f'=IF({w}="B",1,0)', '0'), ('isC', 'Code is C', f'=IF({w}="C",1,0)', '0'),
        ('isD', 'Code is D', f'=IF({w}="D",1,0)', '0'), ('isE', 'Code is E', f'=IF({w}="E",1,0)', '0'),
    ]
    for key, lab, f, fmt in derived:
        put(ws, f'A{r}', lab); put(ws, f'C{r}', f, fmt=fmt); SW[key] = B.name(key, ws, f'C{r}'); r += 1
    derived2 = [
        ('isDE', 'Trust pays leavers and is topped up (D or E)', f"=IF({SW['isD']}+{SW['isE']}>0,1,0)", '0'),
        ('hasWC', 'Worker side is topped up (D, E or A_hold)', f"=IF({SW['isD']}+{SW['isE']}+{SW['isAh']}>0,1,0)", '0'),
        ('pooled', 'One pooled worker fund (E or G)', f"=IF({SW['isE']}+{SW['isG']}>0,1,0)", '0'),
        ('hmult', 'Multiplier on the fitted chance of leaving', f"={SW['turnover']}*IF({SW['isE']}=1,1-{SW['retention']},1)", '0.000'),
        ('capOn', 'Reserve cap in use', f"=IF({SW['cap_on']}=\"Yes\",1,0)", '0'),
        ('covAll', 'Coverage is all U.S.-listed', f"=IF({SW['coverage']}=\"All U.S.-listed\",1,0)", '0'),
        ('carbOn', 'Carbon fee in use', f"=IF({SW['carbon_on']}=\"Yes\",1,0)", '0'),
        ('spread_used', 'Day-one discount spread in use', f"=IF({SW['spread_d1']}>0,{SW['spread_d1']},{B.ref('cy25')})", FMT_P2),
    ]
    for key, lab, f, fmt in derived2:
        put(ws, f'A{r}', lab); put(ws, f'C{r}', f, fmt=fmt); SW[key] = B.name(key, ws, f'C{r}'); r += 1
    # lock shares
    r += 1
    put(ws, f'A{r}', 'Lock rules: share of each line that is locked', 'h'); r += 1
    lock_hdr = r
    for c, h in zip('ABCDEFG', ['Rule', 'Ownership dividend', 'Ad check', 'Carbon check', 'Profit share', 'Worker-trust cash', '']):
        put(ws, f'{c}{r}', h, 'h')
    r += 1
    lock_vals = {'split': (0.5, 0.5, 0.0, 0.5, 0.5), 'half': (0.5,) * 5, 'quarter': (0.25,) * 5, 'none': (0.0,) * 5}
    l0 = r
    for nm in LOCKS:
        put(ws, f'A{r}', nm)
        for c, v in zip('BCDEF', lock_vals[nm]):
            put(ws, f'{c}{r}', v, 'in', fmt=FMT_P)
        r += 1
    put(ws, f'A{r}', 'In use', bold=True)
    for c, key in zip('BCDEF', ['lf', 'la', 'lc', 'lp', 'lw']):
        put(ws, f'{c}{r}', f"=INDEX({c}{l0}:{c}{l0 + 3},MATCH({SW['lock']},$A${l0}:$A${l0 + 3},0))", fmt=FMT_P, bold=True)
        SW[key] = B.name(key, ws, f'{c}{r}')
    r += 2
    # payout rule reference
    put(ws, f'A{r}', 'Payout rules tested (for reference; type one into column G with the setup set to Custom)', 'h'); r += 1
    for c, h in zip('ABCDE', ['Rule', 'Rate', 'Base', 'Limit', 'Share of excess reserve paid a year']):
        put(ws, f'{c}{r}', h, 'h')
    r += 1
    import score as SC
    for nm, p in SC.PAYOUTS.items():
        put(ws, f'A{r}', nm); put(ws, f'B{r}', p['payout_rate'], 'in', fmt=FMT_P)
        put(ws, f'C{r}', p['payout_base'], 'in'); put(ws, f'D{r}', p['cash_cap'], 'in')
        put(ws, f'E{r}', p.get('bonus_spread', 1.0), 'in', fmt=FMT_P)
        r += 1
    for c, wdt in zip('ABCDEFGHKL', [58, 16, 16, 15, 16, 20, 16, 120, 60, 40]):
        ws.column_dimensions[c].width = wdt
    return ws


def build_scenarios(B):
    ws = B.wb['Scenarios']
    put(ws, 'A1', 'Scenarios: the ten market paths', 'title')
    put(ws, 'A2', 'Each path is four rows: real change in company value, cash paid to owners as a share of Jan 1 value, covered jobs, and extra separations. '
                  'The Model reads the path named on the Switches tab. Replays use the history table on the Data tab.', 'note')
    cy = B.ref('cy25')
    blocks = {'g': 6, 'y': 19, 'emp': 32, 'shock': 45}
    titles = {'g': 'Real change in company value (Dec 31 to Dec 31)', 'y': 'Cash paid to owners / value at Jan 1',
              'emp': 'Covered jobs (2025 = 1)', 'shock': 'Extra chance of leaving, every tenure (layoffs)'}
    for k, r0 in blocks.items():
        put(ws, f'A{r0 - 2}', titles[k], 'h')
        put(ws, f'A{r0 - 1}', '#', 'h'); put(ws, f'B{r0 - 1}', 'Path', 'h'); put(ws, f'C{r0 - 1}', 'What it is', 'h')
        for y in range(2021, 2122 if k == 'emp' else 2121):
            put(ws, f'{ycol(y)}{r0 - 1}', str(y), 'h')
        for i, nm in enumerate(SCEN_NAMES):
            put(ws, f'A{r0 + i}', i + 1); put(ws, f'B{r0 + i}', nm); put(ws, f'C{r0 + i}', SCEN_DESC[i], 'note')
    B.addr['scen_rows'] = blocks
    # ---------------- workings (parameters and replay tables) start at row 60
    r = 60
    put(ws, f'A{r}', 'Workings', 'h'); r += 1
    params = [('replay_start', 'First model year of every replay (the fund is full by 2040)', 2046, None),
              ('half_ratio', 'Net-to-gross buyback ratio in the half-offset replays', 0.5, 'R2-33'),
              ('ai_g', 'AI boom: real growth a year, 2026-2035 (BlackRock 15.9% less 2.4% inflation)', 0.132, 'S37'),
              ('ai_y', 'AI boom and cash squeeze: cash paid out falls to (share of value)', 0.015, 'Illustrative (R2-34)'),
              ('ai_jobs', 'AI boom and cash squeeze: covered jobs fall a year, 2026-2035', 0.03, 'Illustrative'),
              ]
    P = {}
    for key, lab, v, src in params:
        put(ws, f'B{r}', lab); put(ws, f'C{r}', v, 'in', fmt=(FMT_P if v < 1 else '0'))
        if src:
            put(ws, f'D{r}', src, 'note')
        P[key] = f'$C${r}'
        r += 1
    put(ws, f'B{r}', 'Prices fall back: real change a year for ten years, (17.44 / 39.58)^(1/10) - 1')
    put(ws, f'C{r}', f"=({B.ref('cape_avg')}/{B.ref('cape_now')})^(1/10)-1", fmt=FMT_P2); P['rev_step'] = f'$C${r}'; r += 1
    put(ws, f'B{r}', 'Prices fall back: cash yield after 2035 (2025 cash on the lower value)')
    put(ws, f'C{r}', f"={cy}/(1+{P['rev_step']})^10", fmt=FMT_P2); P['y_rev'] = f'$C${r}'; r += 2
    # falling profits path (illustrative)
    put(ws, f'A{r}', 'Falling profits and buybacks (illustrative sizes)', 'h'); r += 1
    for c, h in zip('BCDEFGH', ['Year', 'Real change in value', 'Change in cash paid', 'Cash index', 'Value index at Jan 1', 'Cash / Jan 1 value', 'Extra separations']):
        put(ws, f'{c}{r}', h, 'h')
    r += 1
    fall_g = {2046: -0.35, 2047: 0.10, 2048: 0.10, 2049: 0.05, 2050: 0.0}
    fall_c = {2046: -0.30, 2047: -0.30, 2048: 0.40, 2049: 0.20, 2050: 0.10}
    fall_s = {2046: 0.10, 2047: 0.10, 2048: 0.0, 2049: 0.0, 2050: 0.0}
    FALL = {}
    f0 = r
    for y in range(2046, 2051):
        put(ws, f'B{r}', str(y)); put(ws, f'C{r}', fall_g[y], 'in', fmt=FMT_P); put(ws, f'D{r}', fall_c[y], 'in', fmt=FMT_P)
        put(ws, f'E{r}', f'={cy}*(1+D{r})' if y == 2046 else f'=E{r - 1}*(1+D{r})', fmt=FMT_P2)
        put(ws, f'F{r}', 1 if y == 2046 else f'=F{r - 1}*(1+C{r - 1})', 'f', fmt='0.0000')
        put(ws, f'G{r}', f'=E{r}/F{r}', fmt=FMT_P2)
        put(ws, f'H{r}', fall_s[y], 'in', fmt=FMT_P)
        FALL[y] = r
        r += 1
    put(ws, f'B{r}', 'Covered jobs: 2047 0.92, 2048 0.90, 2049 0.94, 2050 0.97, then back to 1 (illustrative)', 'note')
    FALL['emp'] = {2047: 0.92, 2048: 0.90, 2049: 0.94, 2050: 0.97}
    r += 2
    # replay tables
    REP = {}
    for tag, h0, ratio in [('r2000', 2000, None), ('r2008', 2008, None), ('r2000h', 2000, 'half'), ('r2008h', 2008, 'half')]:
        rr = B.ref('net_ratio') if ratio is None else P['half_ratio']
        put(ws, f'A{r}', f"Replay of {h0}-{h0 + 5} onto {2046}-{2051} (net-to-gross buyback ratio {'0.9' if ratio is None else '0.5'})", 'h'); r += 1
        for c, h in zip('BCDEFGHIJK', ['Model year', 'History year', 'Real price change', 'Cash paid that year', 'Cash paid the year before',
                                       'Real change in cash', 'Cash index', 'Value index at Jan 1', 'Cash / Jan 1 value', '']):
            put(ws, f'{c}{r}', h, 'h')
        r += 1
        REP[tag] = {}
        for j in range(6):
            h = h0 + j; hr = HIST_ROW[h]; hp = HIST_ROW[h - 1]
            put(ws, f'B{r}', str(2046 + j)); put(ws, f'C{r}', str(h))
            put(ws, f'D{r}', f'=(1+Data!$B${hr})/(1+Data!$C${hr})-1', fmt=FMT_P2)
            put(ws, f'E{r}', f'=Data!$D${hr}+{rr}*Data!$E${hr}', fmt=FMT_BN)
            put(ws, f'F{r}', f'=Data!$D${hp}+{rr}*Data!$E${hp}', fmt=FMT_BN)
            put(ws, f'G{r}', f'=(E{r}/F{r})/(1+Data!$C${hr})-1', fmt=FMT_P2)
            put(ws, f'H{r}', f'={cy}*(1+G{r})' if j == 0 else f'=H{r - 1}*(1+G{r})', fmt=FMT_P2)
            put(ws, f'I{r}', 1 if j == 0 else f'=I{r - 1}*(1+D{r - 1})', 'f', fmt='0.0000')
            put(ws, f'J{r}', f'=H{r}/I{r}', fmt=FMT_P2)
            REP[tag][2046 + j] = r
            r += 1
        r += 1
    # ---------------- fill the four blocks
    gr, yr_, er, sr = blocks['g'], blocks['y'], blocks['emp'], blocks['shock']
    for i, nm in enumerate(SCEN_NAMES):
        for y in range(2026, 2121):
            c = ycol(y)
            # growth
            if i == 0:
                g = 0
            elif i in (1, 2, 6, 7):
                tag = {1: 'r2000', 2: 'r2008', 6: 'r2000h', 7: 'r2008h'}[i]
                g = f'=$D${REP[tag][y]}' if 2046 <= y <= 2051 else 0
            elif i == 3:
                g = f'=$C${FALL[y]}' if 2046 <= y <= 2050 else 0
            elif i == 4:
                g = f"={P['ai_g']}" if 2026 <= y <= 2035 else 0
            elif i == 5:
                g = f"={P['rev_step']}" if 2026 <= y <= 2035 else 0
            elif i == 8:
                g = 0
            else:  # 9: reversion then 2008
                if 2026 <= y <= 2035:
                    g = f"={P['rev_step']}"
                elif 2046 <= y <= 2051:
                    g = f"=$D${REP['r2008'][y]}"
                else:
                    g = 0
            put(ws, f'{c}{gr + i}', g, 'f', fmt=FMT_P2)
            # yield
            if i == 0:
                yv = f'={cy}'
            elif i in (1, 2, 6, 7):
                tag = {1: 'r2000', 2: 'r2008', 6: 'r2000h', 7: 'r2008h'}[i]
                if y < 2046:
                    yv = f'={cy}'
                elif y <= 2051:
                    yv = f'=$J${REP[tag][y]}'
                else:
                    yv = f'=$J${REP[tag][2051]}'
            elif i == 3:
                yv = f'={cy}' if y < 2046 else (f'=$G${FALL[y]}' if y <= 2050 else f'=$G${FALL[2050]}')
            elif i in (4, 8):
                if y <= 2027:
                    yv = f"={cy}+({P['ai_y']}-{cy})*{y - 2025}/3"
                elif y <= 2035:
                    yv = f"={P['ai_y']}"
                elif y <= 2040:
                    yv = f"={P['ai_y']}+({cy}-{P['ai_y']})*{y - 2035}/5"
                else:
                    yv = f'={cy}'
            elif i == 5:
                yv = f"={cy}/(1+{P['rev_step']})^{y - 2026}" if y <= 2035 else f"={P['y_rev']}"
            else:   # 9
                if y <= 2035:
                    yv = f"={cy}/(1+{P['rev_step']})^{y - 2026}"
                elif y <= 2045:
                    yv = f"={P['y_rev']}"
                else:
                    jr = REP['r2008'][min(y, 2051)]
                    yv = f"=$J${jr}/{cy}*{P['y_rev']}"
            put(ws, f'{c}{yr_ + i}', yv, 'f', fmt=FMT_P2)
            # shock
            if i == 3 and y in (2046, 2047):
                sv = f'=$H${FALL[y]}'
            else:
                sv = 0
            put(ws, f'{c}{sr + i}', sv, 'f', fmt=FMT_P)
        for y in range(2021, 2026):
            put(ws, f'{ycol(y)}{sr + i}', 0, 'f', fmt=FMT_P)
        # jobs, 2021-2121
        for y in range(2021, 2122):
            c = ycol(y); p = ycol(y - 1)
            if i == 3:
                ev = FALL['emp'].get(y, 1.0)
                put(ws, f'{c}{er + i}', ev, 'in' if ev != 1.0 else 'f', fmt='0.000')
                continue
            if i in (4, 8):
                if y <= 2025:
                    ev = 1
                elif y <= 2035:
                    ev = f"={p}{er + i}*(1-{P['ai_jobs']})"
                else:
                    ev = f'={p}{er + i}'
            else:
                ev = 1
            put(ws, f'{c}{er + i}', ev, 'f', fmt='0.000')
    ws.column_dimensions['A'].width = 5; ws.column_dimensions['B'].width = 52; ws.column_dimensions['C'].width = 60
    for y in range(2021, 2122):
        ws.column_dimensions[ycol(y)].width = 9
    ws.freeze_panes = 'D6'
    return ws
