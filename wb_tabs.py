"""Workbook: Ad levy, Joe 40 years, Who paid, Government, Day one."""
from build_wb_part1 import *
from wb_data import DR
from wb_switch import SW, AD_OPTIONS
from wb_model import MR

S = lambda k: SW[k]
X = ycol


def mref(key, y):
    return f'Model!{X(y)}{MR[key]}'


def build_adlevy(B):
    ws = B.wb['Ad levy']
    put(ws, 'A1', 'Ad levy: six ways to set the base', 'title')
    put(ws, 'A2', "No company reports U.S. ad revenue alone, so each firm is a low-high range (R2-23). Rates from Romer's tables (R2-21). "
                  'The option picked on Switches sets the levy as a share of all U.S. internet ad revenue, applied to each year 2021-2025; '
                  'after 2025 the check per person is held at its 2025 level (round one convention).', 'note')
    put(ws, 'A4', 'Firm', 'h'); put(ws, 'B4', 'U.S. digital ad revenue 2025, low ($bn)', 'h'); put(ws, 'C4', 'high ($bn)', 'h')
    put(ws, 'D4', 'middle ($bn)', 'h'); put(ws, 'E4', 'Source', 'h')
    # inputs behind the ranges (R2-22, R2-23)
    put(ws, 'G4', 'Inputs behind the ranges', 'h'); put(ws, 'H4', 'Value', 'h'); put(ws, 'I4', 'Source', 'h')
    inputs = [('iab', 'U.S. internet ad revenue, 2025 ($bn, IAB)', f"=Data!$M${DR['ads']}", 'R2-22', FMT_BN),
              ('tri', 'Google + Meta + Amazon share of U.S. digital ad spending, 2025', 0.72, 'R2-23 (EMARKETER via PPC Land, secondary)', FMT_P),
              ('gww', 'Google advertising, worldwide, 2025 ($bn)', 294.691, 'R2-23 (Alphabet 10-K)', FMT_BN),
              ('gus', "Alphabet's revenue billed to U.S. customers, share of total, 2025", 0.48, 'R2-23 (Alphabet 10-K)', FMT_P),
              ('m_lo', 'Meta revenue billed to U.S. customers, all types, 2025 ($bn)', 74.78, 'R2-23 (Meta 10-K)', FMT_BN),
              ('m_hi', 'Meta U.S. and Canada ad revenue by user location, 2025 ($bn)', 85.278, 'R2-23 (Meta 10-K)', FMT_BN),
              ('a26', 'Amazon U.S. ad revenue, 2026 forecast ($bn)', 56.71, 'R2-23 (EMARKETER)', FMT_BN),
              ('ag', 'Amazon U.S. ad growth forecast, 2026', 0.179, 'R2-23 (EMARKETER)', FMT_P),
              ('tt', 'TikTok U.S. revenue at stake, 2025 ($bn, "nearly $12 billion")', 12.0, 'R2-23 (WARC via Marketing Dive)', FMT_BN),
              ('ms_lo', "Microsoft U.S. ad revenue in Romer's own 2021 inputs ($bn)", 6.65, 'R2-21', FMT_BN),
              ('ms_hi', 'Microsoft search advertising, worldwide, FY2026 ($bn; upper bound)', 15.176, 'R2-23 (Microsoft 10-K)', FMT_BN)]
    IN = {}
    rr = 5
    for key, lab, v, src, fm in inputs:
        put(ws, f'G{rr}', lab); put(ws, f'H{rr}', v, 'in' if not (isinstance(v, str)) else 'link', fmt=fm); put(ws, f'I{rr}', src, 'note')
        IN[key] = f'$H${rr}'; rr += 1
    firms = [('Google', f"={IN['tri']}*{IN['iab']}-B6-B7", f"={IN['gww']}*{IN['gus']}"),
             ('Meta', f"={IN['m_lo']}", f"={IN['m_hi']}"),
             ('Amazon', f"={IN['a26']}/(1+{IN['ag']})", f"={IN['a26']}/(1+{IN['ag']})"),
             ('TikTok', f"={IN['tt']}", f"={IN['tt']}"),
             ('Microsoft', f"={IN['ms_lo']}", f"={IN['ms_hi']}")]
    r = 5
    for nm, lo, hi in firms:
        put(ws, f'A{r}', nm); put(ws, f'B{r}', lo, fmt=FMT_BN); put(ws, f'C{r}', hi, fmt=FMT_BN)
        put(ws, f'D{r}', f'=(B{r}+C{r})/2', fmt=FMT_BN); put(ws, f'E{r}', 'R2-23')
        r += 1
    f0, f1 = 5, r - 1
    put(ws, f'A{r}', 'Google low = the big three\'s share of U.S. spending x the IAB total, less Meta and Amazon. Google high = worldwide Google ads x '
                     "Alphabet's U.S. share of all revenue. Amazon = the 2026 forecast backed out by its growth rate.", 'note')
    r = max(r, rr)
    r += 2
    scheds = [('Romer default schedule', [0, 5, 10, 15, 20, 25, 30, 35, 40, 50, 60], [0, .05, .125, .2, .275, .35, .425, .5, .575, .65, .725]),
              ('Romer alternative schedule', [0, 5, 10, 15, 20, 25], [0, .1, .2, .3, .4, .5]),
              ('Flat 30% above $5 billion', [0, 5], [0, .30]),
              ('0/20/35% steps', [0, 5, 25], [0, .20, .35])]
    SCH = {}
    for nm, b, rt in scheds:
        put(ws, f'A{r}', nm, 'h'); r += 1
        put(ws, f'A{r}', 'Bracket starts at ($bn of a firm\'s U.S. ad revenue)', 'h'); put(ws, f'B{r}', 'Marginal rate', 'h'); put(ws, f'C{r}', 'Rise in rate', 'h'); r += 1
        s0 = r
        for i, (bb, rr) in enumerate(zip(b, rt)):
            put(ws, f'A{r}', bb, 'in', fmt=FMT_BN0); put(ws, f'B{r}', rr, 'in', fmt=FMT_P)
            put(ws, f'C{r}', f'=B{r}' if i == 0 else f'=B{r}-B{r - 1}', fmt=FMT_P)
            r += 1
        SCH[nm] = (s0, r - 1)
        r += 1
    put(ws, f'A{r}', 'The six bases, 2025', 'h'); r += 1
    for c, h in zip('ABCDEFG', ['Base', 'Levy, low ($bn)', 'Levy, middle ($bn)', 'Levy, high ($bn)', 'Per person, middle ($)',
                                'Share of U.S. internet ad revenue (point picked)', 'Note']):
        put(ws, f'{c}{r}', h, 'h')
    r += 1
    opt0 = r
    ads25 = f"Data!$M${DR['ads']}"; pop25 = f"Data!$M${DR['pop']}"
    coll = S('ad_collected')
    pt = S('ad_point')
    for nm in AD_OPTIONS:
        put(ws, f'A{r}', nm)
        if nm.startswith('Targeted ads, 80%'):
            v = f"={ads25}*{S('ad_targeted')}*{S('ad_rate')}*{coll}"
            for c in 'BCD':
                put(ws, f'{c}{r}', v, fmt=FMT_BN)
            put(ws, f'G{r}', '30% x 80% counted as targeted x 95% collected (round one).', 'note')
        elif nm.startswith('Targeted ads, search'):
            v = f"={ads25}*(1-Data!$M${DR['search']})*{S('ad_rate')}*{coll}"
            for c in 'BCD':
                put(ws, f'{c}{r}', v, fmt=FMT_BN)
            put(ws, f'G{r}', 'Everything but search counted as targeted (IAB: search 38.8%).', 'note')
        else:
            s0, s1 = SCH[nm]
            for c, col in zip('BCD', 'BDC'):
                terms = '+'.join(f'SUMPRODUCT($C${s0}:$C${s1},($A${s0}:$A${s1}<{col}{fr})*({col}{fr}-$A${s0}:$A${s1}))'
                                 for fr in range(f0, f1 + 1))
                put(ws, f'{c}{r}', f'=({terms})*{coll}', fmt=FMT_BN)
            put(ws, f'G{r}', 'Firm by firm, then 95% collected. Only five firms clear $5 billion.', 'note')
        put(ws, f'E{r}', f'=C{r}*1E9/{pop25}', fmt=FMT_D)
        put(ws, f'F{r}', f'=IF({pt}="Low",B{r},IF({pt}="High",D{r},C{r}))/{ads25}', fmt=FMT_P2)
        r += 1
    put(ws, f'A{r}', 'In use (Switches)', bold=True)
    put(ws, f'F{r}', f"=INDEX(F{opt0}:F{opt0 + 5},MATCH({S('ad_base')},A{opt0}:A{opt0 + 5},0))", fmt=FMT_P2, bold=True)
    B.name('ad_share', ws, f'F{r}')
    r += 2
    put(ws, f'A{r}', "Romer's own FAQ says the aim is to change behavior, not to raise money; revenue at his top rates would shrink if platforms change their model (R2-21). "
                     "Maryland's ad tax was struck by its Tax Court on Aug 14, 2026 (on appeal); Illinois and Utah taxes start in 2027 and are being sued (R2-24).", 'note')
    for c, wdt in zip('ABCDEFGHI', [44, 22, 18, 18, 18, 24, 60, 14, 40]):
        ws.column_dimensions[c].width = wdt
    return ws


def build_joe(B):
    ws = B.wb['Joe 40 years']
    put(ws, 'A1', "Joe's family, 2021-2060, in 2025 dollars (live)", 'title')
    put(ws, 'A2', "An illustration, not a forecast. Joe is 27 in 2021 and has worked at Walmart since 2016 ($45,000). His wife works part time at a company too small "
                  "to be covered. Kids born 2018 and 2021 take their checks and locked accounts with them at 18. Walmart lays Joe off at the end of 2025; from 2027 he "
                  "works for a smaller, uncovered employer. When the parents' locked account reaches a 10% down payment on a starter home ($260,508) they buy.", 'note')
    hdr = ['Year', 'Kids at home', 'People at home', 'Ownership dividend per person', 'Ad check per person', 'Carbon check per person',
           'Gross carbon fee per person', "Joe's profit share", "Joe's slice of the worker side (share of the company)", 'Worker-side cash to Joe',
           "Joe's own shares (value)", 'Locked per person', 'Spendable per person', "Parents' spendable", "Parents' locked deposits",
           "Kids' spendable", 'Carbon cost in higher prices', 'SPENDABLE NOW', "Parents' locked account before any purchase", 'House bought (year)',
           'Home equity', "Parents' locked account", 'First child\'s locked account', 'Second child\'s locked account',
           'BUILDING (locked account + home equity + own shares)', "Kids' accounts (still at home)"]
    cols = [get_column_letter(i + 1) for i in range(len(hdr))]
    for c, h in zip(cols, hdr):
        put(ws, f'{c}5', h, 'h', wrap=True)
    ws.row_dimensions[5].height = 66
    r0 = 6; years = list(range(2021, 2061)); R = {y: r0 + i for i, y in enumerate(years)}
    isF, isG, isB_, isC, isD, isE, isAh, isAf, pooled = (S(k) for k in ('isF', 'isG', 'isB', 'isC', 'isD', 'isE', 'isAh', 'isAf', 'pooled'))
    lf, la, lc, lp, lw = (S(k) for k in ('lf', 'la', 'lc', 'lp', 'lw'))
    lr = S('lock_return'); house = S('house'); down = S('down')
    br = B.ref('burden_ratio')
    # workings cells below the table
    wk = r0 + len(years) + 2
    put(ws, f'A{wk}', 'Workings', 'h')
    put(ws, f'A{wk + 1}', "Joe's own shares when laid off (vested; 10 years at Walmart)")
    put(ws, f'E{wk + 1}', f"=K{R[2025]}*IF(10>={S('vesting')},1,0)", fmt=FMT_D); V25 = f'$E${wk + 1}'
    put(ws, f'A{wk + 2}', 'Longest wait for leavers in the Model (B only)')
    put(ws, f'E{wk + 2}', f"=MAX(Model!I{MR['wait']}:DD{MR['wait']})", fmt='0'); MW = f'$E${wk + 2}'
    put(ws, f'A{wk + 3}', 'B: year Joe would be paid')
    put(ws, f'E{wk + 3}', f'=2026+MAX(0,{MW}-1)', fmt='0'); PY = f'$E${wk + 3}'
    put(ws, f'A{wk + 4}', "Walmart's 2025 cash yield (what kept shares pay a former worker)")
    put(ws, f'E{wk + 4}', f"={B.ref('wmt_yield')}", 'link', fmt=FMT_P2); WY = f'$E${wk + 4}'
    for y in years:
        r = R[y]; first = (y == 2021)
        put(ws, f'A{r}', y, fmt='0')
        put(ws, f'B{r}', f"=IF(A{r}-{S('kid1')}<18,1,0)+IF(A{r}-{S('kid2')}<18,1,0)", fmt='0')
        put(ws, f'C{r}', f'=2+B{r}', fmt='0')
        put(ws, f'D{r}', f"={mref('fund_pp', y)}", 'link', fmt=FMT_D)
        put(ws, f'E{r}', f"={mref('ad_real', y)}", 'link', fmt=FMT_D)
        put(ws, f'F{r}', f"={mref('carb_real', y)}", 'link', fmt=FMT_D)
        put(ws, f'G{r}', f"={mref('gross_real', y)}", 'link', fmt=FMT_D)
        if y <= 2025:
            put(ws, f'H{r}', f"=MAX(0,MIN({S('ps_rate')}*Data!{X(y)}{DR['wmt_pretax']}*1E6/Data!{X(y)}{DR['wmt_emp']},{S('ps_cap')}*{S('joe_pay')}))*{mref('dfl', y)}", fmt=FMT_D)
            prev = '0' if first else f'I{r - 1}*(1-{mref("i", y)})'
            put(ws, f'I{r}', f"={prev}+{mref('give', y)}/IF({pooled}=1,{B.ref('emp_spx')},Data!{X(y)}{DR['wmt_emp']})", fmt='0.0000000%')
            put(ws, f'J{r}', f"=IF({isF}=1,0,I{r}*IF({pooled}=1,{mref('Yown', y)},Data!{X(y)}{DR['wmt_cash']}*(1-{mref('trim', y)}))*1E9*{mref('pass_ratio', y)}*{mref('dfl', y)})", fmt=FMT_D)
            put(ws, f'K{r}', f"=IF({isF}+{isG}>0,0,I{r}*IF({pooled}=1,{mref('Ve', y)},Data!{X(y)}{DR['wmt_mv']}*(1-{mref('trim', y)}))*1E9*{mref('dfl', y)})", fmt=FMT_D)
        else:
            put(ws, f'H{r}', 0, fmt=FMT_D)
            put(ws, f'J{r}', f"=IF({isD}+{isE}+{isC}>0,IF(A{r}=2026,{V25},0),IF({isAh}+{isAf}>0,{V25}*{WY},IF({isB_}=1,IF(A{r}={PY},{V25},0),0)))", fmt=FMT_D)
            put(ws, f'K{r}', f"=IF({isAh}+{isAf}>0,{V25},IF({isB_}=1,IF(A{r}<{PY},{V25},0),0))", fmt=FMT_D)
        put(ws, f'L{r}', f'={lf}*D{r}+{la}*E{r}+{lc}*F{r}', fmt=FMT_D)
        put(ws, f'M{r}', f'=(1-{lf})*D{r}+(1-{la})*E{r}+(1-{lc})*F{r}', fmt=FMT_D)
        put(ws, f'N{r}', f'=2*M{r}+(1-{lp})*H{r}+(1-{lw})*J{r}', fmt=FMT_D)
        put(ws, f'O{r}', f'=2*L{r}+{lp}*H{r}+{lw}*J{r}', fmt=FMT_D)
        put(ws, f'P{r}', f'=B{r}*M{r}', fmt=FMT_D)
        put(ws, f'Q{r}', f'=C{r}*{br}*G{r}', fmt=FMT_D)
        put(ws, f'R{r}', f'=N{r}+P{r}-Q{r}', fmt=FMT_D, bold=True)
        put(ws, f'S{r}', f'={"0" if first else f"V{r - 1}"}*(1+{lr})+O{r}', fmt=FMT_D)
        put(ws, f'T{r}', (f'=IF(S{r}>={down}*{house},A{r},0)' if first else f'=IF(T{r - 1}>0,T{r - 1},IF(S{r}>={down}*{house},A{r},0))'), fmt='0')
        put(ws, f'U{r}', f'=IF(T{r}>0,{down}*{house},0)', fmt=FMT_D)
        put(ws, f'V{r}', f'=S{r}-IF(T{r}=A{r},{down}*{house},0)', fmt=FMT_D)
        put(ws, f'W{r}', f"=IF(A{r}-{S('kid1')}<18,{'0' if first else f'W{r - 1}'}*(1+{lr})+L{r},0)", fmt=FMT_D)
        put(ws, f'X{r}', f"=IF(A{r}-{S('kid2')}<18,{'0' if first else f'X{r - 1}'}*(1+{lr})+L{r},0)", fmt=FMT_D)
        put(ws, f'Y{r}', f'=V{r}+U{r}+K{r}', fmt=FMT_D, bold=True)
        put(ws, f'Z{r}', f'=W{r}+X{r}', fmt=FMT_D)
    last = R[2060]
    s = wk + 6
    put(ws, f'A{s}', 'Summary', 'h'); s += 1
    put(ws, f'A{s}', 'House bought in'); put(ws, f'E{s}', f'=IF(MAX(T{r0}:T{last})>0,MAX(T{r0}:T{last}),"not by 2060")', fmt='0', bold=True)
    B.name('joe_house', ws, f'E{s}'); s += 1
    put(ws, f'A{s}', 'First child takes at 18'); put(ws, f'E{s}', f"=INDEX(W{r0}:W{last},MATCH({S('kid1')}+17,A{r0}:A{last},0))", fmt=FMT_D, bold=True)
    B.name('joe_kid1', ws, f'E{s}'); s += 1
    put(ws, f'A{s}', 'Second child takes at 18'); put(ws, f'E{s}', f"=INDEX(X{r0}:X{last},MATCH({S('kid2')}+17,A{r0}:A{last},0))", fmt=FMT_D, bold=True)
    B.name('joe_kid2', ws, f'E{s}'); s += 1
    for y in (2025, 2026, 2030, 2040, 2050, 2060):
        put(ws, f'A{s}', f'{y}: spendable now / building'); put(ws, f'E{s}', f'=R{R[y]}', fmt=FMT_D, bold=True)
        put(ws, f'F{s}', f'=Y{R[y]}', fmt=FMT_D, bold=True)
        B.name(f'joe_spend{y}', ws, f'E{s}'); B.name(f'joe_build{y}', ws, f'F{s}')
        s += 1
    s += 1
    put(ws, f'A{s}', "Does the spendable part of the carbon check cover the family's higher prices? (2025, per person)", 'h'); s += 1
    put(ws, f'A{s}', 'Spendable carbon check per person'); put(ws, f'E{s}', f"={mref('carb_real', 2025)}*(1-{lc})", fmt=FMT_D); a = s; s += 1
    put(ws, f'A{s}', "Middle family's higher prices per person"); put(ws, f'E{s}', f"={br}*{mref('gross_real', 2025)}", fmt=FMT_D); b = s; s += 1
    put(ws, f'A{s}', 'Left over (+) or out of pocket (-)'); put(ws, f'E{s}', f'=E{a}-E{b}', fmt=FMT_D, bold=True); s += 1
    put(ws, f'A{s}', "With half the carbon check locked (the essay's rule) and a full rebate, about $44 a person is left; with a 75% rebate the family is $38 a person short each year until the lock opens.", 'note')
    ws.column_dimensions['A'].width = 8
    for c in cols[1:]:
        ws.column_dimensions[c].width = 13
    ws.column_dimensions['A'].width = 34
    ws.freeze_panes = 'B6'
    return ws


def build_whopaid(B):
    ws = B.wb['Who paid']
    put(ws, 'A1', 'Who paid, 2021-2025 (live: reads the setup on Switches)', 'title')
    put(ws, 'A2', "Round one counted the new shares' full value. Part of it only offset the trusts' own dilution, and part was companies joining the index. "
                  "Both are now separate. With the setup set to Round one bookkeeping this tab shows the reviewers' numbers: net $2.56 trillion.", 'note')
    yrs = list(range(2021, 2026)); C = {y: get_column_letter(3 + i) for i, y in enumerate(yrs)}
    put(ws, 'A4', 'Line', 'h'); put(ws, 'B4', 'Unit', 'h')
    for y in yrs:
        put(ws, f'{C[y]}4', str(y), 'h')
    put(ws, 'H4', '5-year total', 'h'); put(ws, 'I4', 'How it is calculated', 'h'); put(ws, 'J4', 'Source', 'h')
    r = 5
    L = {}

    def line(key, label, unit, fn, how='', src='', fmt=FMT_BN, total=True, bold=False):
        nonlocal r
        put(ws, f'A{r}', label, bold=bold); put(ws, f'B{r}', unit)
        for y in yrs:
            put(ws, f'{C[y]}{r}', fn(y), fmt=fmt, bold=bold)
        if total:
            put(ws, f'H{r}', f'=SUM(C{r}:G{r})', fmt=fmt, bold=bold)
        put(ws, f'I{r}', how, 'note'); put(ws, f'J{r}', src)
        L[key] = r; r += 1

    put(ws, f'A{r}', 'A. The net transfer', 'h'); r += 1
    line('i', 'New shares issued (share of each company)', 'share', lambda y: f"={mref('i', y)}", 'Model', fmt='0.00%', total=False)
    line('Vj', 'What the covered companies were worth on Jan 1, after the trim', '$ billions', lambda y: f"={mref('Vj', y)}", 'Model', total=False)
    line('new', 'Value of the new shares', '$ billions', lambda y: f"={C[y]}{L['i']}*{C[y]}{L['Vj']}", 'Round one counted this ($2.65 trillion)')
    line('own', "Trusts' own holdings before the issue", 'share',
         lambda y: f"={mref('c_end', y - 1)}+{mref('w3', y - 1)}+{mref('q3', y - 1)}+{mref('pool3', y - 1)}", 'Citizen fund + worker trust at the prior Dec 31', fmt='0.00%', total=False)
    line('self', "Part that only offsets the trusts' own dilution", '$ billions', lambda y: f"={C[y]}{L['i']}*{C[y]}{L['own']}*{C[y]}{L['Vj']}",
         'New shares dilute the trusts too; that part moves nothing from anyone else')
    line('net', 'NET TRANSFER from the people who owned the companies', '$ billions', lambda y: f"={C[y]}{L['new']}-{C[y]}{L['self']}", bold=True)
    line('memo', 'Memo: stakes in companies that joined the index (a change in what is counted)', '$ billions',
         lambda y: (f"=({mref('c1', y)}+{mref('w2', y)}+{mref('q1', y)})*({mref('Ve', y)}-{mref('Vj', y)}*(1+Data!{X(y)}{DR['price']})"
                    f"+Data!{X(y)}{DR['netbb']}*{mref('scale', y)}*(1-{mref('trim', y)}))"),
         'Trusts\' stake x (Dec 31 value - Jan 1 value x price return + net buybacks). Not a transfer.', 'S09')
    r += 1
    put(ws, f'A{r}', 'B. Who gave it up', 'h'); r += 1
    line('fs', "Foreign investors' share of U.S. public company stock (prior Q4)", '%', lambda y: f"=Data!{X(y - 1)}{DR['foreign']}", fmt=FMT_P, total=False, src='S11')
    line('foreign', 'Given up by foreign investors', '$ billions', lambda y: f"={C[y]}{L['net']}*{C[y]}{L['fs']}")
    line('us', 'Given up by U.S. holders (households, pensions, endowments, insurers)', '$ billions', lambda y: f"={C[y]}{L['net']}-{C[y]}{L['foreign']}",
         'Pension and insurer holdings spread over households by stock exposure (a simplification)')
    for i, g in enumerate(DR['groups']):
        line(f'g{i}', f'   {g} of households', '$ billions', lambda y, i=i: f"={C[y]}{L['us']}*Data!{X(y - 1)}{DR['stock_share0'] + i}",
             "U.S. share x group's share of stock exposure at the prior Q4", 'S12')
    r += 1
    put(ws, f'A{r}', 'C. Who got it', 'h'); r += 1
    line('cit', 'Citizen fund, net of its own dilution', '$ billions',
         lambda y: f"=({mref('ac', y)}-{mref('i', y)}*{mref('c_end', y - 1)})*{mref('Vj', y)}", 'Its new shares less its own dilution')
    line('wkr', 'Worker side, net of its own dilution', '$ billions', lambda y: f"={C[y]}{L['net']}-{C[y]}{L['cit']}",
         "Who these workers are by wealth isn't in public data, so it isn't guessed")
    for i, g in enumerate(DR['groups']):
        line(f'c{i}', f'   {g} of households, from the citizen fund', '$ billions',
             lambda y, i=i: f"={C[y]}{L['cit']}*Data!{X(y - 1)}{DR['hh_share0'] + i}", 'Equal per household as a stand-in for equal per person', 'S12')
    r += 1
    put(ws, f'A{r}', 'D. Net for each group from the citizen fund alone (worker side left out)', 'h'); r += 1
    for i, g in enumerate(DR['groups']):
        line(f'n{i}', f'   {g} of households', '$ billions', lambda y, i=i: f"={C[y]}{L[f'c{i}']}-{C[y]}{L[f'g{i}']}")
    line('nf', '   Foreign investors', '$ billions', lambda y: f"=-{C[y]}{L['foreign']}")
    r += 1
    put(ws, f'A{r}', "E. The trusts' cash in 2021-2025", 'h'); r += 1
    line('wcash', "Worker side's cash (its share of dividends and buybacks)", '$ billions', lambda y: f"={mref('tcash', y)}",
         'Round one never said where this went. Now: to current workers or to leavers, by the exit switch.')
    line('ccash', "Citizen fund's cash", '$ billions', lambda y: f"={mref('cash_c', y)}")
    B.name('wp_net', ws, f"H{L['net']}"); B.name('wp_self', ws, f"H{L['self']}"); B.name('wp_memo', ws, f"H{L['memo']}")
    B.name('wp_new', ws, f"H{L['new']}"); B.name('wp_wcash', ws, f"H{L['wcash']}")
    ws.column_dimensions['A'].width = 70; ws.column_dimensions['B'].width = 12
    for c in 'CDEFGH':
        ws.column_dimensions[c].width = 12
    ws.column_dimensions['I'].width = 70; ws.column_dimensions['J'].width = 8
    return ws


def build_government(B):
    ws = B.wb['Government']
    put(ws, 'A1', "The government's side, in 2025 dollars (live)", 'title')
    put(ws, 'A2', 'What the plan does to the federal budget, as if it were running: 2025 and 2040, plus the five backtest years added up. '
                  'Upper bounds where noted. Plus = money in, minus = money lost.', 'note')
    put(ws, 'A4', 'Line', 'h'); put(ws, 'B4', '2025', 'h'); put(ws, 'C4', '2040', 'h'); put(ws, 'D4', 'How it is calculated', 'h'); put(ws, 'E4', 'Source', 'h')
    put(ws, 'F4', "2021-2025 total (each year's dollars)", 'h', wrap=True)
    r = 5; L = {}
    ps = f"{S('ps_rate')}*Data!$M${DR['pretax']}"
    ps5 = f"{S('ps_rate')}*SUM(Data!$I${DR['pretax']}:$M${DR['pretax']})"
    off = B.ref('offset')
    Y5 = range(2021, 2026)

    def line(key, label, f25, f40, how, src='', fmt=FMT_BN, bold=False, f5=None):
        nonlocal r
        put(ws, f'A{r}', label, bold=bold); put(ws, f'B{r}', f25, fmt=fmt, bold=bold); put(ws, f'C{r}', f40, fmt=fmt, bold=bold)
        put(ws, f'D{r}', how, 'note'); put(ws, f'E{r}', src)
        if f5 is not None:
            put(ws, f'F{r}', f5, fmt=fmt, bold=bold)
        L[key] = r; r += 1

    line('coll', 'Carbon fee collected (memo)', f"={mref('coll', 2025)}*{mref('dfl', 2025)}", f"={mref('coll', 2040)}",
         'From the Model', fmt=FMT_BN, f5='=' + '+'.join(mref('coll', y) for y in Y5))
    cf = f"*(1-{S('collect')}-(1-{S('collect')})*{S('rebate')}-{off})"
    line('carb', 'Carbon fee: kept minus rebates, minus the 25% offset', f"=B{r - 1}{cf}", f"=C{r - 1}{cf}",
         "A fee raises prices, so taxable income falls; Treasury's convention is 25% of the gross fee. A 75% rebate covers it.", 'R2-04',
         f5=f"=F{r - 1}{cf}")
    line('ps', 'Profit share paid (memo: 10% of all domestic corporate pre-tax profit, held at 2025)', f'={ps}', f'={ps}', 'Upper bound: every corporation, no pay cap', 'S23',
         f5=f'={ps5}')
    line('corp', 'Profit share: corporate tax lost (it is deductible pay)', f'=-0.21*B{L["ps"]}', f'=-0.21*C{L["ps"]}', '21% federal rate (26 U.S.C. 11(b))',
         f5=f'=-0.21*F{L["ps"]}')
    line('inc', 'Profit share: income tax workers pay on it', f'=0.18*B{L["ps"]}', f'=0.18*C{L["ps"]}', "CBO's average marginal rate on labor income, income tax part", 'R2-07',
         f5=f'=0.18*F{L["ps"]}')
    line('pay', 'Profit share: payroll tax, only if the law counts it as wages', f'=0.09*B{L["ps"]}', f'=0.09*C{L["ps"]}', "CBO's payroll part; a legal choice", 'R2-07',
         f5=f'=0.09*F{L["ps"]}')
    line('ads', 'Ad levy: the same 25% offset', f"=-{off}*{mref('ad_levy', 2025)}", f"=-{off}*{mref('ad_levy', 2040)}", 'The levy is a deductible cost for the platforms', 'R2-04',
         f5=f"=-{off}*(" + '+'.join(mref('ad_levy', y) for y in Y5) + ')')
    line('trust', "Dividend and gains tax the trusts don't pay", f"=-({mref('c_end', 2025)}+{mref('w3', 2025)})*{mref('Yown', 2025)}*0.27*0.2",
         f"=-({mref('c_end', 2040)}+{mref('w3', 2040)})*{mref('Yown', 2040)}*0.27*0.2",
         'Trust stake x cash paid x 27% of stock in taxable accounts x 20% top rate. Needs an explicit exemption in law.', 'R2-06, R2-35',
         f5='=-(' + '+'.join(f"({mref('c_end', y)}+{mref('w3', y)})*{mref('Yown', y)}" for y in Y5) + ')*0.27*0.2')
    line('tot', 'NET for the budget, with payroll tax', f'=B{L["carb"]}+B{L["corp"]}+B{L["inc"]}+B{L["pay"]}+B{L["ads"]}+B{L["trust"]}',
         f'=C{L["carb"]}+C{L["corp"]}+C{L["inc"]}+C{L["pay"]}+C{L["ads"]}+C{L["trust"]}', '', bold=True,
         f5=f'=F{L["carb"]}+F{L["corp"]}+F{L["inc"]}+F{L["pay"]}+F{L["ads"]}+F{L["trust"]}')
    line('tot2', 'NET for the budget, without payroll tax', f'=B{L["tot"]}-B{L["pay"]}', f'=C{L["tot"]}-C{L["pay"]}', '', bold=True,
         f5=f'=F{L["tot"]}-F{L["pay"]}')
    line('gdp', 'As a share of GDP, without payroll tax (2025 GDP; the five-year column uses 2021-2025 GDP)', f"=B{L['tot2']}/Data!$M${DR['gdp']}",
         f"=C{L['tot2']}/Data!$M${DR['gdp']}", '2040 is shown against 2025 GDP for scale', 'S24', fmt=FMT_P2,
         f5=f"=F{L['tot2']}/SUM(Data!$I${DR['gdp']}:$M${DR['gdp']})")
    line('gdp2', 'As a share of GDP, with payroll tax', f"=B{L['tot']}/Data!$M${DR['gdp']}",
         f"=C{L['tot']}/Data!$M${DR['gdp']}", '', 'S24', fmt=FMT_P2,
         f5=f"=F{L['tot']}/SUM(Data!$I${DR['gdp']}:$M${DR['gdp']})")
    B.name('gov_carb25', ws, f"B{L['carb']}"); B.name('gov_tot25', ws, f"B{L['tot2']}"); B.name('gov_tot40', ws, f"C{L['tot2']}")
    r += 1
    put(ws, f'A{r}', "Two ways to close the carbon gap: send back 75% of the fee instead of all of it (the check falls by a quarter), or make the rebate taxable "
                     "and open to everyone, which JCT scores with no offset (R2-04). The second keeps the full check but taxes it. Either way only the carbon line evens out.", 'note')
    ws.column_dimensions['A'].width = 72; ws.column_dimensions['B'].width = 12; ws.column_dimensions['C'].width = 12; ws.column_dimensions['D'].width = 90
    ws.column_dimensions['E'].width = 14; ws.column_dimensions['F'].width = 16
    return ws


def build_dayone(B):
    ws = B.wb['Day one']
    put(ws, 'A1', 'Day-one drop: a valuation scenario, not bookkeeping (live)', 'title')
    put(ws, 'A2', "If markets priced the plan's whole path the day it became law, existing shares would fall by about the value of everything they give up: the shares "
                  "issued over the years (the 2020 owners' falling share), the profit share's trim, and any cash companies pay leavers. "
                  "Discounted at the cash yield. The money doesn't vanish: it moves to the trusts and to workers.", 'note')
    yrs = list(range(2021, 2121))
    put(ws, 'A4', 'Line', 'h')
    for y in yrs:
        put(ws, f'{X(y)}4', str(y), 'h')
    sp = S('spread_used')
    put(ws, 'A5', 'Years from 2021')
    put(ws, 'A6', "2020 owners' share (Model)")
    put(ws, 'A7', 'Share of cash that still reaches owners (1 unless companies pay leavers)')
    put(ws, 'A8', 'Weight (1-d) x d^t, d = 1/(1+spread)')
    put(ws, 'A9', 'Weighted share kept')
    for y in yrs:
        c = X(y)
        put(ws, f'{c}5', y - 2021, fmt='0')
        put(ws, f'{c}6', f"={mref('legacy', y)}", 'link', fmt=FMT_P2)
        put(ws, f'{c}7', f"=IF({mref('Yown', y)}+{mref('comp_cash', y)}>0,1-{mref('comp_cash', y)}/({mref('Yown', y)}+{mref('comp_cash', y)}),1)", fmt=FMT_P2)
        put(ws, f'{c}8', f'=(1-1/(1+{sp}))*(1/(1+{sp}))^{c}5', fmt='0.00000')
        put(ws, f'{c}9', f'={c}8*{c}6*{c}7', fmt='0.00000')
    r = 11
    put(ws, f'A{r}', 'Result', 'h'); r += 1
    put(ws, f'A{r}', 'Discount spread used'); put(ws, f'B{r}', f'={sp}', fmt=FMT_P2); rsp = r; r += 1
    put(ws, f'A{r}', 'd = 1/(1+spread)'); put(ws, f'B{r}', f'=1/(1+B{rsp})', fmt='0.000000'); rd = r; r += 1
    put(ws, f'A{r}', 'Share kept, 2021-2120'); put(ws, f'B{r}', f'=SUM({X(2021)}9:{X(2120)}9)', fmt='0.000000'); rs = r; r += 1
    put(ws, f'A{r}', "Yearly rate of change in the owners' share, 2100-2120 (carried 100 more years)")
    a, z = X(2100), X(2120)
    put(ws, f'B{r}', f'=IF({a}6>0,({z}6/{a}6)^(1/20),1)', fmt='0.000000'); rr = r; r += 1
    put(ws, f'A{r}', 'Share kept after 2120')
    put(ws, f'B{r}', f'=(1-B{rd})*B{rd}^100*B{rr}*{z}6*{z}7*(1-(B{rd}*B{rr})^100)/(1-B{rd}*B{rr})+B{rd}^200*{z}6*B{rr}^100*{z}7', fmt='0.000000'); rt = r; r += 1
    put(ws, f'A{r}', 'DROP IN EXISTING SHARES ON DAY ONE', bold=True)
    put(ws, f'B{r}', f"=1-(B{rs}+B{rt})*(1-{mref('trim', 2120)})", fmt=FMT_P, bold=True); rdrop = r
    B.name('d1_drop', ws, f'B{r}'); r += 2
    put(ws, f'A{r}', 'Where the money goes (2025 values)', 'h'); r += 1
    v25 = mref('Vraw', 2025)
    put(ws, f'A{r}', 'Total fall in existing shares ($ billions)'); put(ws, f'B{r}', f'=B{rdrop}*{v25}', fmt=FMT_BN0); rtot = r; r += 1
    put(ws, f'A{r}', "To workers through the profit share (the trim's value)"); put(ws, f'B{r}', f"={mref('trim', 2120)}*{v25}", fmt=FMT_BN0); r += 1
    put(ws, f'A{r}', 'To the trusts through new shares'); put(ws, f'B{r}', f'=B{rtot}-B{r - 1}', fmt=FMT_BN0); rtr = r; r += 1
    put(ws, f'A{r}', '   of which the citizen fund'); put(ws, f'B{r}', f"=B{rtr}*(1-{S('alpha_eff')})", fmt=FMT_BN0); rc = r; r += 1
    put(ws, f'A{r}', '   of which the worker side'); put(ws, f'B{r}', f"=B{rtr}*{S('alpha_eff')}", fmt=FMT_BN0); r += 1
    put(ws, f'A{r}', 'Citizen fund share per person ($)'); put(ws, f'B{r}', f"=B{rc}*1E9/Data!$M${DR['pop']}", fmt=FMT_D); B.name('d1_pp', ws, f'B{r}'); r += 1
    put(ws, f'A{r}', 'Share of the fall borne by foreign investors'); put(ws, f'B{r}', f"=Data!$M${DR['foreign']}", 'link', fmt=FMT_P); r += 2
    put(ws, f'A{r}', 'This is a valuation scenario: real prices would move on news, rates and behavior, and the split by wealth inside the U.S. share is not guessed. '
                     'Split between the trusts uses the share of new shares each gets (C and payouts to leavers are counted as cash the owners give up).', 'note')
    ws.column_dimensions['A'].width = 70
    ws.freeze_panes = 'B5'
    return ws
