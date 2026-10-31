"""Workbook: Stress tests, Best combination, Number labels, Engine check, Start here."""
import json, os
from build_wb_part1 import *
from wb_data import DR
from wb_switch import SW, SCEN_NAMES
from wb_model import MR
import engine as E, scenarios as Sc, score as SC

S = lambda k: SW[k]
X = ycol
RES = json.load(open(os.path.join(HERE, 'results.json')))
CC = json.load(open(os.path.join(HERE, 'closecalls.json')))
P10 = dict(payout_rate=0.80, payout_base='cash_avg5', cash_cap='cash_res', bonus_spread=0.2)
SCEN_ALL = Sc.all_market() + Sc.harsher() + [Sc.reversion_then_crash()]
assert [s.name for s in SCEN_ALL] == SCEN_NAMES, 'scenario order must match the Scenarios tab'
PASSF = lambda ok: 'PASS' if ok else 'FAIL'


def mr(key, y):
    return f'Model!{X(y)}{MR[key]}'


def rng(key, y0, y1):
    return f'Model!{X(y0)}{MR[key]}:{X(y1)}{MR[key]}'


def build_stress(B):
    ws = B.wb['Stress tests']
    put(ws, 'A1', 'Stress tests', 'title')
    put(ws, 'A2', 'Part A scores whatever is set on Switches (setup and path) live. Parts B and C are the engine runs behind the report: '
                  'the winning setup on all ten paths, and the carbon and ad tests.', 'note')
    r = 4
    put(ws, f'A{r}', 'A. The setup and path on Switches, scored live', 'h'); r += 1
    put(ws, f'A{r}', 'Setup:'); put(ws, f'B{r}', f"={S('preset')}", 'link'); put(ws, f'C{r}', 'Path:'); put(ws, f'D{r}', f"={S('scenario')}", 'link'); r += 1
    for c, h in zip('ABCD', ['Pass line', 'Line', 'This run', 'Result']):
        put(ws, f'{c}{r}', h, 'h')
    r += 1
    rows = [
        ('Largest one-year fall in the ownership dividend, after inflation (2026-2120)', S('pl_fund'),
         f"=MAX(0,-MIN({rng('fund_yoy', 2026, 2120)}))", 'le', FMT_P),
        ('Largest one-year fall in the whole check (dividend, ads, carbon)', S('pl_whole'),
         f"=MAX(0,-MIN({rng('whole_yoy', 2026, 2120)}))", 'le', FMT_P),
        ('Years the fund sells shares to pay checks (minimum reserve: zero, never sell)', 0,
         f"=COUNTIF({rng('sold_c', 2026, 2120)},\">0\")", 'le', '0'),
        ("2020 owners' share of the companies in 2050", S('pl_leg30'), f"={mr('legacy', 2050)}", 'ge', FMT_P),
        ("2020 owners' share in 2120", S('pl_leg100'), f"={mr('legacy', 2120)}", 'ge', FMT_P),
        ('Most new shares in one year once the trusts are full (the engine checks this on stress paths)', S('pl_issue'),
         f"=MAX({rng('topup_post', 2026, 2120)})", 'le', '0.000%'),
        ('Longest wait for a leaver to be paid (years)', S('pl_wait'), f"=MAX({rng('wait', 2021, 2120)})", 'le', '0'),
    ]
    a0 = r
    for lab, line, val, op, fm in rows:
        put(ws, f'A{r}', lab); put(ws, f'B{r}', f'={line}' if isinstance(line, str) else line, 'link' if isinstance(line, str) else 'in', fmt=fm)
        put(ws, f'C{r}', val, fmt=fm, bold=True)
        put(ws, f'D{r}', f'=IF(C{r}<=B{r}+1E-9,"PASS","FAIL")' if op == 'le' else f'=IF(C{r}>=B{r}-1E-9,"PASS","FAIL")', bold=True)
        r += 1
    put(ws, f'A{r}', 'All lines', bold=True); put(ws, f'D{r}', f'=IF(COUNTIF(D{a0}:D{r - 1},"FAIL")=0,"PASS","FAIL")', bold=True)
    B.name('live_all', ws, f'D{r}'); r += 2
    put(ws, f'A{r}', 'What this run pays', 'h'); r += 1
    for lab, f, fm in [('Ownership dividend per person in 2030 (2025 dollars)', f"={mr('fund_pp', 2030)}", FMT_D),
                       ('Ownership dividend per person in 2040', f"={mr('fund_pp', 2040)}", FMT_D),
                       ('Ownership dividend per person in 2050', f"={mr('fund_pp', 2050)}", FMT_D),
                       ('Ownership dividend per person in 2070', f"={mr('fund_pp', 2070)}", FMT_D),
                       ('Whole check per person in 2040 (dividend, ads, carbon)', f"={mr('whole', 2040)}", FMT_D),
                       ('Worker side in 2050: paid to leavers plus passed to current workers ($ billions)', f"={mr('wk_pay', 2050)}", FMT_BN),
                       ('Trusts reach the target in', f"={B.ref('fill_year')}", '0')]:
        put(ws, f'A{r}', lab); put(ws, f'C{r}', f, fmt=fm, bold=True); r += 1
    r += 1
    # ---------------- B: winner on all ten paths (engine)
    put(ws, f'A{r}', 'B. The winning setup on all ten paths (engine: engine.py, scenarios.py, score.py)', 'h'); r += 1
    hdr = ['Path', 'Largest fall in the ownership dividend', 'Largest fall in the whole check', 'Years selling shares',
           'Most new shares once full', 'Longest wait (years)', 'Dividend in 2050 (2025 $)', 'Result']
    for c, h in zip('ABCDEFGH', hdr):
        put(ws, f'{c}{r}', h, 'h', wrap=True)
    r += 1
    win = E.Design(name='Winning setup', worker='F', **P10)
    res = SC.evaluate(win, SCEN_ALL)
    for sc in SCEN_ALL:
        v = res['by_scen'][sc.name]
        ok = (v['fund_drop'] <= SC.PASS['fund_drop'] + 1e-9 and v['whole_drop'] <= SC.PASS['whole_drop'] + 1e-9 and v['sales_years'] == 0
              and v['max_issue_post'] <= SC.PASS['stress_issue'] + 1e-9 and v['max_wait'] <= SC.PASS['wait'])
        put(ws, f'A{r}', sc.name)
        put(ws, f'B{r}', v['fund_drop'], 'in', fmt=FMT_P); put(ws, f'C{r}', v['whole_drop'], 'in', fmt=FMT_P)
        put(ws, f'D{r}', v['sales_years'], 'in', fmt='0'); put(ws, f'E{r}', v['max_issue_post'], 'in', fmt='0.000%')
        put(ws, f'F{r}', v['max_wait'], 'in', fmt='0'); put(ws, f'G{r}', v['r']['check_pp_real'][2050], 'in', fmt=FMT_D)
        put(ws, f'H{r}', PASSF(ok), bold=True)
        r += 1
    put(ws, f'A{r}', 'Blue = values written by the engine. Set Switches to Winning setup and pick a path to see the same numbers computed live in Part A.', 'note'); r += 2
    # ---------------- C: carbon and ads (engine)
    put(ws, f'A{r}', 'C. The carbon and ad tests, winning setup (engine)', 'h'); r += 1
    hdr = ['Test', 'Whole check 2025', 'Whole check 2030', 'Whole check 2040', 'Whole check 2050', 'Whole check 2070',
           'Largest one-year fall in the whole check', 'Carbon check 2040', 'Carbon check 2070', 'Ownership dividend passes the carbon check in']
    for c, h in zip('ABCDEFGHIJ', hdr):
        put(ws, f'{c}{r}', h, 'h', wrap=True)
    r += 1
    for nm, v in CC['pipes'].items():
        put(ws, f'A{r}', nm[0].upper() + nm[1:])
        for c, k in zip('BCDEF', ['whole2025', 'whole2030', 'whole2040', 'whole2050', 'whole2070']):
            put(ws, f'{c}{r}', v[k], 'in', fmt=FMT_D)
        put(ws, f'G{r}', max(0.0, v['worst_whole']), 'in', fmt=FMT_P)
        put(ws, f'H{r}', v['carbon2040'], 'in', fmt=FMT_D); put(ws, f'I{r}', v['carbon2070'], 'in', fmt=FMT_D)
        fy = v['first_year_fund_above_carbon']
        put(ws, f'J{r}', (str(fy) if fy else 'never') if nm != 'no carbon' else 'n/a')
        r += 1
    put(ws, f'A{r}', 'Per person a year, 2025 dollars. Carbon checks after 2035 extend the fee path past the last year any source projects (RFF stops at 2035).', 'note'); r += 2
    put(ws, f'A{r}', 'D. What each path is', 'h'); r += 1
    import wb_switch
    for nm, ds in zip(SCEN_NAMES, wb_switch.SCEN_DESC):
        put(ws, f'A{r}', nm); put(ws, f'B{r}', ds, 'note'); r += 1
    ws.column_dimensions['A'].width = 80
    for c in 'BCDEFGHIJ':
        ws.column_dimensions[c].width = 15
    return ws


def build_best(B):
    ws = B.wb['Best combination']
    put(ws, 'A1', 'Best combination', 'title')
    put(ws, 'A2', 'Every setting was run on ten market paths and scored on four pass lines set before the runs (Switches). '
                  'Only setups that pass all four are compared on the five tests. Blue values are engine output (engine subfolder).', 'note')
    r = 4
    put(ws, f'A{r}', 'A. The setup that holds up best', 'h'); r += 1
    lines = [
        ('Worker exit', "F: the whole quarter goes to the citizen fund. Workers keep the profit share (10% of pre-tax profit, capped at three months' pay), paid every year, half in cash and half into their own locked account, so nothing is owed when they leave. G and A_forever also pass; whether workers should own a piece too is yours."),
        ('Payout rule', "80% of the fund's stake times the five-year average cash companies paid owners (after the trim, after inflation). Never more than cash in plus the reserve. Reserve capped at two years of checks; a fifth of anything above is paid out each year."),
        ('Lock', 'Carbon checks fully spendable; half of the ownership dividend, the ad check and the profit share locked. The level is a value choice (yours). With a 75% rebate the numbers force carbon to stay unlocked; with the full rebate that is yours too.'),
        ('Carbon', 'In, with the full fee sent back (value choice: it costs the Treasury about $56 billion a year in 2025 terms; sending back 75% makes the carbon line pay for itself, at a smaller check).'),
        ('Ad levy', "30% of each company's U.S. digital ad revenue above $5 billion: a base that can be measured once companies have to report it (a judgment, not a number), raising about what round one's targeted base did ($172 to $231 a person, middle $201, against $197). The totals here and the pass-line runs still carry round one's $197 line. Flat or Romer's rising rates is yours; whether a federal levy survives the courts is legal."),
        ('Coverage', 'S&P 500 companies first; all U.S.-listed adds about 18% to the check; private companies later (legal and data).'),
    ]
    for k, v in lines:
        put(ws, f'A{r}', k, bold=True); put(ws, f'B{r}', v, wrap=False); r += 1
    r += 1
    wp = RES['win_path']
    put(ws, f'A{r}', 'What it does (engine, central path)', 'h'); r += 1
    facts = [('Ownership dividend per person, 2030 (2025 dollars)', wp['2030']['fund'], FMT_D),
             ('Ownership dividend per person, 2040', wp['2040']['fund'], FMT_D),
             ('Ownership dividend per person, 2050', wp['2050']['fund'], FMT_D),
             ("2020 owners' share of the companies, 2050 and every year after", wp['2050']['legacy'], FMT_P),
             ('New shares needed once the trusts are full (2041-2120)', max(wp[str(y)]['issue'] for y in range(2041, 2121)), '0.000%'),
             ('Largest one-year fall in the ownership dividend, all ten paths', max(CC[list(CC.keys())[0]]['drops'].values()), FMT_P),
             ('Years the fund sells shares to pay checks, all ten paths', CC[list(CC.keys())[0]]['sales'], '0'),
             ('Leavers who wait to be paid', 0, '0')]
    for lab, v, fm in facts:
        put(ws, f'A{r}', lab); put(ws, f'B{r}', v, 'in', fmt=fm); r += 1
    r += 1
    put(ws, f'A{r}', 'B. Why it wins', 'h'); r += 1
    er = RES['exit_rates']
    why = [
        f"1. A worker trust that pays leavers out needs new shares forever. People who leave take about {er['value_weighted'] * 100:.1f}% of its value a year "
        f"(fitted to BLS tenure), while its cash covers {er['cash_yield'] * 100:.1f}%. D, E and A_hold all fail the no-new-shares-forever line.",
        '2. The ways around that fail other lines: B (pay leavers only from the trust\'s cash) makes them wait about 31 years; C (companies pay leavers cash) takes '
        'the cash the citizen fund lives on, and its check collapses.',
        '3. Three settings pass all four lines: F, G and A_forever. F pays the citizen fund twice as much ($891 against $445 a person in 2040) because it gets all of the new shares.',
        "4. Of ten payout rules, only the cash-based one passes. Rules that pay 2.5% or 3% of the fund's value pay out more than companies hand over at today's 2.7% "
        'cash yield, so they sell shares on the central path or fall 25% or more in a cash squeeze.',
    ]
    for t in why:
        put(ws, f'A{r}', t); r += 1
    r += 1
    put(ws, f'A{r}', 'C. Close calls (the numbers can\'t separate these)', 'h'); r += 1
    for c, h in zip('ABCDEFGH', ['Variant of the payout rule', 'Passes all lines', 'Dividend 2030', 'Dividend 2040', 'Dividend 2050',
                                 'Paid out 2026-2060 ($ billions, 2025 $)', 'Largest fall, ten paths', 'Cash squeeze fall']):
        put(ws, f'{c}{r}', h, 'h', wrap=True)
    r += 1
    sq = 'Cash squeeze without the boom'
    for nm, v in CC.items():
        if nm == 'pipes':
            continue
        put(ws, f'A{r}', nm); put(ws, f'B{r}', 'Yes' if v['pass_']['all'] else 'No', bold=True)
        put(ws, f'C{r}', v['fund2030'], 'in', fmt=FMT_D); put(ws, f'D{r}', v['fund2040'], 'in', fmt=FMT_D); put(ws, f'E{r}', v['fund2050'], 'in', fmt=FMT_D)
        put(ws, f'F{r}', v['total_paid_2026_2060'], 'in', fmt=FMT_BN0); put(ws, f'G{r}', v['worst'], 'in', fmt=FMT_P); put(ws, f'H{r}', v['drops'][sq], 'in', fmt=FMT_P)
        r += 1
    put(ws, f'A{r}', 'Rates from 75% to 85% and reserve caps from one to three years all pass. Higher rates and smaller reserves pay a little more and fall further in a '
                     'bad year. 80% and two years sits in the middle, 1.5 points inside the 15% line. G and A_forever tie with each other on everything the citizen fund sees.', 'note')
    r += 2
    put(ws, f'A{r}', "D. Value calls: choices the numbers can't settle", 'h'); r += 1
    calls = [
        '1. Whether workers get a stake of their own (F, A_forever or G). A_forever lets leavers keep their shares and still passes every line, but it halves the ownership dividend ($445 against $891 a person in 2040).',
        '2. How much of the rest of each check to lock: split, a quarter, half or none. The Joe 40 years tab shows what each does to spendable money and to what the family builds.',
        "3. The carbon rebate: all of the fee tax-free (the Treasury covers about $56 billion a year), 75% (the carbon line pays for itself, at a smaller check), or all of it taxable.",
        "4. Whether the ad rate stays flat at 30% above $5 billion or climbs with company size the way Romer designed it. Whether a federal levy survives the courts is legal: Maryland's ad tax was struck in August 2026 and is on appeal.",
        '5. The reserve: one, two or three years of checks (and the payout rate, 75% to 85%). It trades about 3% of total payouts either way against how far a 2008-style slide goes (34%, 30% or 24%).',
        '6. The pass lines themselves: 15% and 10% falls, 73% and 70% kept by 2020 owners, 0.5% top-ups, six years for leavers.',
        '7. Private and foreign companies: whether and how to cover them (law and missing data, not arithmetic).',
    ]
    for t in calls:
        put(ws, f'A{r}', t); r += 1
    r += 1
    # ---------------- scoreboard
    put(ws, f'A{r}', 'E. The scoreboard: every worker-exit setting with three payout rules (engine)', 'h'); r += 1
    hdr = ['Worker exit', 'Payout rule', 'Falls within 15% and 10%', 'Never sells shares to pay checks', 'No new shares forever',
           'Leavers paid within six years', 'ALL FOUR', 'Dividend 2040', 'Dividend 2050', "2020 owners' share 2050", "2020 owners' share 2120",
           'Largest fall, ten paths', 'Longest wait (years)', 'New shares a year, 2050-2120']
    cols = [get_column_letter(i + 1) for i in range(len(hdr))]
    for c, h in zip(cols, hdr):
        put(ws, f'{c}{r}', h, 'h', wrap=True)
    ws.row_dimensions[r].height = 54
    r += 1
    plabel = {'P1': '3% of Jan 1 value', 'P9': '2.5% of 5-yr avg value, capped', 'P10': '80% of 5-yr avg cash, capped'}
    for b in RES['board']:
        vals = [b['worker'], plabel[b['payout']], PASSF(b['PL1']), PASSF(b['PL2']), PASSF(b['PL3']), PASSF(b['PL4']), PASSF(b['all']),
                float(b['fund2040']), float(b['fund2050']), float(b['legacy2050']), float(b['legacy2120']), float(b['worst_drop']),
                float(b['max_wait']), float(b['topup_lr'])]
        fms = [None, None, None, None, None, None, None, FMT_D, FMT_D, FMT_P, FMT_P, FMT_P, '0', '0.00%']
        for c, v, fm in zip(cols, vals, fms):
            put(ws, f'{c}{r}', v, 'in' if isinstance(v, float) else 'f', fmt=fm, bold=(c == 'G'),
                fill=(GREEN_F if (c == 'G' and b['all']) else None))
        r += 1
    put(ws, f'A{r}', "Codes: F all to the citizen fund; G pooled worker fund, income only; A_forever leavers keep shares, still counted; A_hold kept while held; "
                     "B trust buys leavers out from its cash; C companies pay leavers cash; D trust pays leavers, then tops up; E portable account (retention 10% or 30%). "
                     "'+vest3' = three-year cliff; '+cap100k' = per-person cap of $100,000 with overflow to the citizen fund.", 'note')
    r += 2
    put(ws, f'A{r}', 'F. Ten payout rules on the winning worker setting (F), all ten paths (engine)', 'h'); r += 1
    hdr = ['Rule', 'What it pays', 'ALL FOUR', 'Dividend 2030', 'Dividend 2040', 'Dividend 2050', "2020 owners' share 2120",
           'First year selling shares (central)', 'Largest fall, ten paths']
    for c, h in zip('ABCDEFGHI', hdr):
        put(ws, f'{c}{r}', h, 'h', wrap=True)
    r += 1
    for p in RES['payout_rules']:
        vals = [p['rule'], p['label'], PASSF(p['all']), float(p['fund2030']), float(p['fund2040']), float(p['fund2050']),
                float(p['legacy2120']), (p['first_sale'] if p['first_sale'] not in (None, 'None') else 'never'),
                max(float(x) for x in p['drops'].values())]
        fms = [None, None, None, FMT_D, FMT_D, FMT_D, FMT_P, '0', FMT_P]
        for c, v, fm in zip('ABCDEFGHI', vals, fms):
            put(ws, f'{c}{r}', v, 'in' if isinstance(v, float) else 'f', fmt=fm, bold=(c == 'C'))
        r += 1
    ws.column_dimensions['A'].width = 62; ws.column_dimensions['B'].width = 34
    for c in cols[2:]:
        ws.column_dimensions[c].width = 14
    return ws


LABELS = [
    # number, what, label, where
    ('$2.56 trillion', 'Net transfer from 2020 owners into the trusts, 2021-2025, round-one settings', 'Calculated', 'Who paid (Round one bookkeeping setup)'),
    ('$85 billion', "Part of round one's $2.65 trillion that only offset the trusts' own dilution", 'Calculated', 'Who paid'),
    ('$220 billion', 'Stakes in companies joining the index: a change in what is counted, not a transfer', 'Calculated', 'Who paid (memo line)'),
    ('2.70%', 'Cash paid to owners in 2025 as a share of the Dec 31, 2025 value (dividends plus net buybacks; 2.6986% unrounded)', 'Calculated from measured', 'Data'),
    ('1.04x to 1.36x', 'Cash coverage of the checks, 2021-2025, round-one settings', 'Calculated', 'Model'),
    ('0.98x', 'Coverage in 2025 if net buybacks were 10% lower; the reserve covers it', 'Calculated', 'Model (Switches: coverage test)'),
    ('25%', 'Share of a carbon fee lost to lower income and payroll taxes', 'Calculated (official scorekeeping convention)', 'Data; Government'),
    ('$56 billion a year', 'Treasury cost of sending back the whole carbon fee, 2025 terms', 'Calculated', 'Government'),
    ('0.43', "Middle family's carbon cost per person as a share of the gross fee per person", 'Calculated from measured', 'Data'),
    ('$146 billion', "Worker trust's cash, 2021-2025, round-one settings", 'Calculated', 'Who paid'),
    ('12.2% a year', "Share of a worker trust's value that leavers take out each year", 'Calculated from measured (BLS tenure fit)', 'Workers; engine'),
    ('23.3% a year', 'Share of covered workers who leave each year in the fitted model (JOLTS large firms: 18-23%)', 'Calculated from measured', 'Workers'),
    ('$464 / $891 / $972', 'Ownership dividend per person in 2030 / 2040 / 2050, winning setup, 2025 dollars', 'Calculated on an illustrative path', 'Model; Best combination'),
    ('$445', 'Ownership dividend per person in 2040 if half the new shares go to workers (A_forever or G)', 'Calculated on an illustrative path', 'Best combination'),
    ('$1,074 / $1,386 / $1,984 / $2,291', 'Whole check per person (ownership dividend, ads, carbon), 2025 / 2030 / 2040 / 2050, winning setup, 2025 dollars', 'Calculated; after 2025 on an illustrative path, and carbon after 2035 extends the fee rule', 'Model'),
    ('$420 / $661 / $1,087 / $1,169', 'The floor without carbon (no fee, no rebate, no higher prices): ownership dividend plus ads, same years', 'Calculated on an illustrative path', 'Model (Switches: carbon off)'),
    ('$690 billion', 'Reserve in 2040, winning setup (about two years of checks), 2025 dollars', 'Calculated on an illustrative path', 'Model'),
    ('$529 billion / $10.2 billion', 'Lowest reserve after the fill in the 2008-2009 replay / lowest reserve in the cash squeeze (2030)', 'Calculated on a historical replay / on an illustrative path', 'Stress tests'),
    ('75%', "2020 owners' share of the companies once the trusts are full, winning setup", 'Calculated (plan rule)', 'Model'),
    ('13.5%', 'Largest one-year fall in the ownership dividend across ten paths (2008-2009 replay)', 'Calculated on a historical replay', 'Stress tests'),
    ('31 years', 'How long leavers wait when the trust buys them out only from its own cash (B)', 'Calculated', 'Best combination'),
    ('27% / 28% / 40%', 'Day-one drop: winning setup / round one / essay with real turnover', 'Illustrative (valuation scenario)', 'Day one'),
    ('$16 trillion; $10.7 trillion; $31,000', 'Day-one fall in existing shares; the part that goes to the citizen fund; per person', 'Illustrative (valuation scenario)', 'Day one'),
    ('29%', 'Share of U.S. public company stock held abroad (who bears that part of any fall)', 'Measured', 'Data'),
    ('About 0% / about 100%', "France: profit share taken back out of base pay, most workers / high-skill workers", 'Measured (study)', 'Sources R2-18'),
    ('$654 / $897', 'Carbon check per person, 2025 / 2040 (2025 dollars)', 'Calculated; after 2035 illustrative (no source projects the fee path)', 'Model'),
    ('2032', 'Year the ownership dividend passes the carbon check if emissions fall 7.5% a year', 'Calculated on an illustrative path', 'Stress tests'),
    ('$197', 'Ad check per person, round-one base (80% of ads counted as targeted); the totals and pass-line runs use it', 'Calculated on an assumption nobody measures', 'Ad levy'),
    ('$201 (range $172 to $231)', "Ad check per person, flat 30% of each company's U.S. digital ad revenue above $5 billion, 2025", 'Calculated from measured and estimated firm revenue (low to high)', 'Ad levy'),
    ('$252 to $380', "Ad check per person under Romer's default schedule (low to high firm revenue)", 'Calculated from measured ranges', 'Ad levy'),
    ('+18%', 'Rise in the ownership dividend if all U.S.-listed companies are covered', 'Calculated from measured', 'Best combination; Model'),
    ('2043', "Year Joe's family can make a 10% down payment on a starter home (split lock)", 'Illustrative (life events)', 'Joe 40 years'),
    ('$3,026 / $52,378', "Joe's family: spendable in 2025 / building by 2060 (split lock), 2025 dollars", 'Illustrative (life events)', 'Joe 40 years'),
    ('$4,877 / $6,813', "What each of Joe's kids takes at 18 (split lock)", 'Illustrative', 'Joe 40 years'),
    ('9%', "Profit share's trim on company values and payouts", 'Calculated (round one)', 'Switches'),
    ('-$77B / +$66B / +$33B', 'Profit share: corporate tax lost / income tax paid on it / payroll tax if it counts as wages', 'Calculated upper bound; payroll is legal', 'Government'),
    ('-$383 billion / -$232 billion', 'Net federal budget effect over 2021-2025, without / with payroll tax on the profit share (0.3% / 0.2% of GDP a year)', 'Calculated; the payroll piece is legal', 'Government'),
    ('80% and two years', 'Payout rate and reserve cap in the winning setup', 'Value choice within the range the numbers allow', 'Switches'),
    ('Split lock', 'Carbon checks spendable, half of the rest locked', 'Value choice', 'Switches'),
    ('15%, 10%, 73%, 70%, 0.5%, six years', 'The pass lines', 'Value choice', 'Switches'),
    ('Three-year cliff; six-year schedule', 'Longest vesting and payout schedules federal law allows employee plans', 'Legal', 'Sources R2-16'),
    ('Tax exemption for the trusts', 'A federal citizen trust would need an explicit exemption', 'Legal', 'Sources R2-35'),
    ("Each company's U.S. digital ad revenue", "The ad levy's base, instead of 'targeted' ads", "Legal (companies would have to report it); picking a base that can be measured is a judgment, not a number", 'Ad levy'),
    ('Flat 30% above $5 billion, or rising rates', "The ad levy's rate (Romer's schedule rises to 72.5%)", 'Value choice; whether a federal levy survives the courts is legal', 'Ad levy'),
    ('20% a year', "Share of former workers' shares sold each year (A_hold only)", 'Behavior (not measured)', 'Switches'),
    ('1.5% cash yield', 'Cash paid out during the AI-building years in the AI and cash-squeeze tests', 'Illustrative', 'Scenarios'),
]


def build_labels(B):
    ws = B.wb['Number labels']
    put(ws, 'A1', 'Number labels: what kind of number each headline is', 'title')
    put(ws, 'A2', 'Measured = read from a source. Calculated = arithmetic on measured numbers and stated rules. Illustrative = a path or life event picked to show '
                  'how the plan behaves, not a forecast. Behavior = how people or markets would act (not measured). Legal = depends on law or courts. '
                  'Value choice = what people want; numbers can inform it but not settle it.', 'note')
    for c, h in zip('ABCDE', ['#', 'Number', 'What it is', 'Label', 'Where']):
        put(ws, f'{c}4', h, 'h')
    r = 5
    for i, (n, what, lab, where) in enumerate(LABELS, 1):
        put(ws, f'A{r}', i); put(ws, f'B{r}', n, bold=True); put(ws, f'C{r}', what); put(ws, f'D{r}', lab); put(ws, f'E{r}', where)
        r += 1
    ws.column_dimensions['A'].width = 5; ws.column_dimensions['B'].width = 30; ws.column_dimensions['C'].width = 90
    ws.column_dimensions['D'].width = 52; ws.column_dimensions['E'].width = 34
    return ws


def build_check(B, tested=None):
    ws = B.wb['Engine check']
    put(ws, 'A1', 'Engine check: the live Model against the engine', 'title')
    put(ws, 'A2', 'The engine (Python, engine subfolder) and this workbook are two separate builds of the same rules. With Switches on a named setup and the '
                  'central path, the differences below should be zero to rounding.', 'note')
    central = SCEN_NAMES[0]
    put(ws, 'A4', 'Status', bold=True)
    put(ws, 'B4', f"=IF(AND({S('preset')}<>\"Custom\",{S('scenario')}=\"{central}\"),\"Comparing the live Model with the engine's \"&{S('preset')},"
                  f"\"Switches are not on a named setup with the central path, so the differences are not meaningful\")", bold=True)
    designs = {'Winning setup': E.Design(worker='F', **P10),
               'Essay as written': E.Design(worker='D'),
               'Round one bookkeeping': E.Design(worker='D', turnover_scale=0.0, reserve_cap_years=None)}
    runs = {k: E.run(d) for k, d in designs.items()}
    for c, n in zip('IJK', designs.keys()):
        put(ws, f'{c}1', n, 'note')
    yrs = [2021, 2022, 2023, 2024, 2025, 2030, 2035, 2040, 2045, 2050, 2070, 2100, 2120]
    items = [('fund_pp', 'Ownership dividend per person, 2025 $', 'check_pp_real', FMT_D, 1.0),
             ('legacy', "2020 owners' share", 'legacy', '0.0000%', 1.0),
             ('c_end', 'Citizen fund stake', 'c', '0.0000%', 1.0),
             ('reserve', 'Reserve ($ billions, as of that year)', 'reserve', FMT_BN, 1.0)]
    r = 6
    names = list(designs.keys())
    for key, lab, ek, fm, _ in items:
        put(ws, f'A{r}', lab, 'h'); r += 1
        put(ws, f'A{r}', 'Year', 'h')
        heads = ['Engine: ' + n for n in names] + ['Engine, setup in use', 'Live Model', 'Difference']
        for c, h in zip('BCDEFG', heads):
            put(ws, f'{c}{r}', h, 'h', wrap=True)
        r += 1
        for y in yrs:
            put(ws, f'A{r}', str(y))
            for c, n in zip('BCD', names):
                put(ws, f'{c}{r}', float(runs[n][ek][y]), 'in', fmt=fm)
            put(ws, f'E{r}', f"=IF({S('preset')}=\"Custom\",\"\",INDEX(B{r}:D{r},MATCH({S('preset')},$I$1:$K$1,0)))", fmt=fm)
            put(ws, f'F{r}', f"={mr(key, y)}", 'link', fmt=fm)
            put(ws, f'G{r}', f'=IF(E{r}="","",F{r}-E{r})', fmt=('0.000000' if fm != FMT_D else '0.0000'))
            r += 1
        r += 1
    if tested:
        put(ws, f'A{r}', 'Combinations recalculated in this workbook and compared with the engine (central path, 2021-2120, every year)', 'h'); r += 1
        for c, h in zip('ABCDE', ['Setting tested', 'Largest gap in the ownership dividend ($ per person)', "Largest gap in 2020 owners' share",
                                  'Largest gap in the citizen stake', 'Result']):
            put(ws, f'{c}{r}', h, 'h', wrap=True)
        r += 1
        for t in tested:
            put(ws, f'A{r}', t['name']); put(ws, f'B{r}', t['fund'], 'in', fmt='0.0000'); put(ws, f'C{r}', t['legacy'], 'in', fmt='0.00000000')
            put(ws, f'D{r}', t['c'], 'in', fmt='0.00000000'); put(ws, f'E{r}', t['result'], bold=True)
            r += 1
        put(ws, f'A{r}', 'The per-person cap on worker stakes works by company value per employee (ten groups), which the workbook does not carry; it runs in the engine only.', 'note')
    ws.column_dimensions['A'].width = 48
    for c in 'BCDEFG':
        ws.column_dimensions[c].width = 17
    return ws


def build_start(B):
    ws = B.wb['Start here']
    put(ws, 'A1', 'Everybody Owns a Piece, round two: the switches', 'title')
    put(ws, 'A2', f'Built Oct 19, 2026. Every open choice in the plan is a switch on the Switches tab; the Model recalculates the plan from 2021 to 2120 for whatever is set.', 'note')
    r = 4
    put(ws, f'A{r}', 'The answer', 'h'); r += 1
    ans = [
        "The setup that holds up best puts the whole quarter in the citizen fund, keeps the profit share for workers, and pays the fund out of the cash it actually receives: "
        "80% of the five-year average, with a two-year reserve.",
        'It passes every pass line on all ten market paths: the ownership dividend never falls more than 13.5% in a year, the fund never sells shares, '
        "no new shares are needed after 2040, and nobody waits to be paid.",
        'It pays $464 a person in 2030, $891 in 2040 and $972 in 2050 (2025 dollars), before carbon and ads.',
        "What's left is yours: whether workers also get a stake, how much to lock, the carbon rebate, whether the ad rate climbs with company size, the reserve size, the pass lines, and private and foreign companies.",
    ]
    for t in ans:
        put(ws, f'A{r}', t); r += 1
    r += 1
    put(ws, f'A{r}', 'How to use it', 'h'); r += 1
    for t in ['1. Switches: pick Winning setup, Essay as written, Round one bookkeeping, or Custom (then change the yellow cells in column G).',
              '2. Switches: pick a market path, the carbon and ad settings, and the lock rule.',
              '3. Read the results on Stress tests (part A is live), Joe 40 years, Who paid, Government and Day one.',
              '4. Best combination holds the full engine scoreboard and the reasoning. Engine check shows the live Model matching the engine.']:
        put(ws, f'A{r}', t); r += 1
    r += 1
    put(ws, f'A{r}', 'Tabs', 'h'); r += 1
    tabs = [('Switches', 'Every choice, three named setups, pass lines, and the derived flags the Model reads'),
            ('Best combination', 'The winner, why, the close calls, your calls, and the full scoreboard (engine)'),
            ('Stress tests', 'Live pass lines for the setup and path picked; the winner on all ten paths (engine)'),
            ('Model', 'The plan year by year, 2016-2120: shares, cash, checks, carbon, ads (live)'),
            ('Workers', 'Who works at covered companies, by years with the employer, and the shares they hold (live)'),
            ('Scenarios', 'The ten market paths, including replays of 2000-2005 and 2008-2013 built from history'),
            ('Joe 40 years', "Joe's family from 2021 to 2060: spendable now and what they're building, every year (live)"),
            ('Who paid', 'Net transfer, own dilution, index memo, who gave up what and who got it (live)'),
            ('Government', 'Carbon offset, profit-share taxes, ad levy, trust tax exemption (live)'),
            ('Day one', 'The day-one drop as a valuation scenario, and where the money goes (live)'),
            ('Ad levy', 'Six ways to set the ad base, firm by firm'),
            ('Number labels', 'Every headline number labeled measured, calculated, illustrative, behavior, legal or value choice'),
            ('Engine check', 'The live Model against the engine'),
            ('Data', 'Measured inputs, each with a source ID'),
            ('Sources', 'S01-S55 (round one) and R2-01 to R2-41 (round two)')]
    for t, d in tabs:
        put(ws, f'A{r}', t, bold=True); put(ws, f'B{r}', d); r += 1
    r += 1
    put(ws, f'A{r}', 'Colors', 'h'); r += 1
    put(ws, f'A{r}', 'Blue', 'in'); put(ws, f'B{r}', 'Typed in from a source, or a value written by the engine'); r += 1
    put(ws, f'A{r}', 'Black'); put(ws, f'B{r}', 'Calculated in this workbook'); r += 1
    put(ws, f'A{r}', 'Green', 'link'); put(ws, f'B{r}', 'Pulled from another tab'); r += 1
    put(ws, f'A{r}', 'Yellow', fill=YELLOW); put(ws, f'B{r}', 'A switch you can change'); r += 1
    ws.column_dimensions['A'].width = 24; ws.column_dimensions['B'].width = 120
    for rr in range(5, 9):
        ws.merge_cells(f'A{rr}:B{rr}')
    return ws
