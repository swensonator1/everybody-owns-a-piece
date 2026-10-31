"""Workbook: Workers grid and the live Model (2016-2120)."""
from build_wb_part1 import *
from wb_data import DR
from wb_switch import SW

MR = {}
WR = dict(n0=8, n45=53, staysum=54, stay44=55, hires=56, tot=57, h0=60, h45=105, u0=108, u45=153)
Y_START = 2021


def S(k):
    return SW[k]


def build_workers(B):
    ws = B.wb['Workers']
    put(ws, 'A1', 'Workers: who is at a covered company, how likely they are to leave, and how many shares each holds', 'title')
    put(ws, 'A2', 'Three grids by years with the employer (rows, 0-45) and calendar year (columns). Shares are fractions of the covered companies '
                  'per unit of workforce, so the Model can count what leavers take each year. Read by Model rows 52-53.', 'note')
    for y in range(Y_START, 2121):
        put(ws, f'{ycol(y)}4', str(y), 'h')
    put(ws, 'A4', 'Years with employer', 'h'); put(ws, 'B4', 'Chance of leaving', 'h'); put(ws, 'C4', 'Survival / vested', 'h')
    put(ws, 'A6', 'A. Share of covered workers by years with the employer (start of each year; each column sums to 1)', 'h')
    put(ws, 'B7', 'fitted (Data)', 'note'); put(ws, 'C7', 'survival from hire', 'note')
    hz = DR['haz0']
    for k in range(46):
        r = WR['n0'] + k
        put(ws, f'A{r}', k)
        band = 0 if k == 0 else (1 if k <= 2 else (2 if k <= 9 else (3 if k <= 19 else (4 if k <= 44 else 5))))
        put(ws, f'B{r}', f'=Data!$D${hz + band}', 'link', fmt=FMT_P2)
        put(ws, f'C{r}', 1 if k == 0 else f'=C{r - 1}*(1-B{r - 1})', 'f', fmt='0.000000')
        for y in range(Y_START, 2121):
            X = ycol(y); P = ycol(y - 1)
            if y == Y_START:
                f = f'=$C{r}/SUM($C${WR["n0"]}:$C${WR["n45"]})'
            elif k == 0:
                f = f'=IF({P}${WR["tot"]}>0,{P}${WR["hires"]}/{P}${WR["tot"]},0)'
            else:
                f = f'=IF({P}${WR["tot"]}>0,{P}{r - 1}*(1-{P}{WR["h0"] + k - 1})/{P}${WR["tot"]},0)'
            put(ws, f'{X}{r}', f, fmt='0.000000')
    for key, lab in [('staysum', 'Staying to next year (all)'), ('stay44', 'Staying, excluding year 45'),
                     ('hires', 'Hires needed for next year'), ('tot', 'Workforce next year before rescaling')]:
        r = WR[key]
        put(ws, f'A{r}', lab, bold=True)
        for y in range(Y_START, 2121):
            X = ycol(y); N = ycol(y + 1)
            n_rng = f'{X}{WR["n0"]}:{X}{WR["n45"]}'; h_rng = f'{X}{WR["h0"]}:{X}{WR["h45"]}'
            if key == 'staysum':
                f = f'=SUM({n_rng})-SUMPRODUCT({n_rng},{h_rng})'
            elif key == 'stay44':
                f = f'={X}{WR["staysum"]}-{X}{WR["n45"]}*(1-{X}{WR["h45"]})'
            elif key == 'hires':
                f = f'=MAX(0,Model!{N}${MR["emp"]}/Model!{X}${MR["emp"]}-{X}{WR["staysum"]})'
            else:
                f = f'={X}{WR["stay44"]}+{X}{WR["hires"]}'
            put(ws, f'{X}{r}', f, fmt='0.000000')
    put(ws, f'A{WR["h0"] - 2}', 'B. Chance of leaving during the year (fitted rate x switches, plus layoffs and shrinking jobs)', 'h')
    put(ws, f'B{WR["h0"] - 1}', 'used', 'note'); put(ws, f'C{WR["h0"] - 1}', 'vested (1/0)', 'note')
    for k in range(46):
        r = WR['h0'] + k; rn = WR['n0'] + k
        put(ws, f'A{r}', k)
        if k == 45:
            put(ws, f'B{r}', f"=IF({S('turnover')}>0,1,B{rn}*{S('hmult')})", fmt=FMT_P2)
        else:
            put(ws, f'B{r}', f"=B{rn}*{S('hmult')}", fmt=FMT_P2)
        put(ws, f'C{r}', f"=IF(A{r}>={S('vesting')},1,0)", fmt='0')
        for y in range(Y_START, 2121):
            X = ycol(y); N = ycol(y + 1)
            put(ws, f'{X}{r}', f'=MIN(1,$B{r}+Model!{X}${MR["shock"]}+MAX(0,1-Model!{N}${MR["emp"]}/Model!{X}${MR["emp"]}))', fmt='0.0000')
    put(ws, f'A{WR["u0"] - 2}', "C. Shares held per unit of workforce, after the Jan 1 issue (fraction of the covered companies)", 'h')
    for k in range(46):
        r = WR['u0'] + k
        put(ws, f'A{r}', k)
        for y in range(Y_START, 2121):
            X = ycol(y); P = ycol(y - 1)
            if y == Y_START or k == 0:
                f = f'=Model!{X}${MR["give"]}'
            else:
                f = f'={P}{r - 1}*IF({P}${WR["tot"]}>0,{P}${WR["tot"]},1)*(1-Model!{X}${MR["i"]})+Model!{X}${MR["give"]}'
            put(ws, f'{X}{r}', f, fmt='0.0000000')
    # fit check: steady-state tenure mix (mid-year presence) vs BLS Table 3
    r = WR['u45'] + 3
    put(ws, f'A{r}', 'Fit check: steady-state tenure mix from the fitted rates vs BLS January 2026 (Table 3)', 'h'); r += 1
    put(ws, f'A{r}', 'Years', 'h'); put(ws, f'B{r}', 'Model', 'h'); put(ws, f'C{r}', 'BLS', 'h'); r += 1
    pres = f'$C${WR["n0"]}:$C${WR["n45"]}'
    bands = [(0, 0), (1, 1), (2, 2), (3, 4), (5, 9), (10, 14), (15, 19), (20, 45)]
    labels = ['Under 1', '1 to 2', '2 to 3', '3 to 5', '5 to 10', '10 to 15', '15 to 20', '20 or more']
    tot = f'SUMPRODUCT({pres},1-$B${WR["n0"]}:$B${WR["n45"]}/2)'
    for i, ((a, b), lab) in enumerate(zip(bands, labels)):
        ra, rb = WR['n0'] + a, WR['n0'] + b
        put(ws, f'A{r}', lab)
        put(ws, f'B{r}', f'=SUMPRODUCT($C${ra}:$C${rb},1-$B${ra}:$B${rb}/2)/{tot}', fmt=FMT_P)
        put(ws, f'C{r}', f'=Data!$D${DR["bls0"] + i}', 'link', fmt=FMT_P)
        r += 1
    put(ws, f'A{r}', 'The fit pools 1 to 5 years because the 2021-22 hiring wave left a bulge at 3-4 years in the January 2026 count.', 'note')
    ws.column_dimensions['A'].width = 30; ws.column_dimensions['B'].width = 12; ws.column_dimensions['C'].width = 12
    ws.freeze_panes = 'D5'
    return ws


def build_model(B):
    ws = B.wb['Model']
    put(ws, 'A1', 'Model: the plan, one year at a time (live; reads the Switches tab)', 'title')
    put(ws, 'A2', '2021-2025 run on what happened (nominal dollars, as paid). 2026 onward runs in 2025 dollars on the path picked on Switches. '
                  'Shares are fractions of the covered companies. The 2020 column holds the starting state.', 'note')
    put(ws, 'A3', 'Trusts reach the target in', bold=True)
    for y in range(2016, 2122):
        put(ws, f'{ycol(y)}4', str(y), 'h')
    put(ws, 'A4', 'Line', 'h'); put(ws, 'B4', 'Unit', 'h'); put(ws, 'C4', 'Note', 'h')
    sc = S('scenario')
    sr = B.addr['scen_rows']
    rows = {}

    def row(key, r, label, unit='', note=''):
        MR[key] = r
        put(ws, f'A{r}', label); put(ws, f'B{r}', unit)
        if note:
            put(ws, f'C{r}', note, 'note')

    def fill(key, years, fn, fmt=None, kind='f'):
        r = MR[key]
        for y in years:
            v = fn(y)
            if v is None:
                continue
            put(ws, f'{ycol(y)}{r}', v, kind, fmt=fmt)

    ALL = range(2016, 2121); RUN = range(2021, 2121)
    X = ycol; P = lambda y: ycol(y - 1); N = lambda y: ycol(y + 1)

    put(ws, 'A5', 'A. The covered companies', 'h')
    row('year', 6, 'Year')
    fill('year', range(2016, 2122), lambda y: y, fmt='0')
    row('cpi', 7, 'Consumer prices (CPI-U)', 'index')
    fill('cpi', ALL, lambda y: f'=Data!{X(y)}25' if y <= 2025 else '=Data!$M$25', fmt='0.000', kind='link')
    row('dfl', 8, 'Multiplier to 2025 dollars', 'x')
    fill('dfl', ALL, lambda y: f'=Data!$M$25/{X(y)}7', fmt='0.0000')
    row('scale', 9, 'Coverage multiple (1 = S&P 500)', 'x', 'All U.S.-listed / S&P 500 when switched')
    fill('scale', ALL, lambda y: f"=IF({S('covAll')}=1,Data!{X(min(max(y, 2020), 2025))}21,1)", fmt='0.000')
    row('g', 10, 'Real change in company value (path)', '%', 'From Scenarios')
    fill('g', range(2026, 2121), lambda y: f"=INDEX(Scenarios!{X(y)}${sr['g']}:{X(y)}${sr['g'] + 9},MATCH({sc},Scenarios!$B${sr['g']}:$B${sr['g'] + 9},0))", fmt=FMT_P2, kind='link')
    row('yield', 11, 'Cash paid to owners / Jan 1 value (path)', '%', 'From Scenarios')
    fill('yield', range(2026, 2121), lambda y: f"=INDEX(Scenarios!{X(y)}${sr['y']}:{X(y)}${sr['y'] + 9},MATCH({sc},Scenarios!$B${sr['y']}:$B${sr['y'] + 9},0))", fmt=FMT_P2, kind='link')
    MR['emp'] = 12
    put(ws, 'A12', 'Covered jobs (2025 = 1, path)'); put(ws, 'B12', 'index'); put(ws, 'C12', 'From Scenarios', 'note')
    fill('emp', range(2021, 2122), lambda y: f"=INDEX(Scenarios!{X(y)}${sr['emp']}:{X(y)}${sr['emp'] + 9},MATCH({sc},Scenarios!$B${sr['emp']}:$B${sr['emp'] + 9},0))", fmt='0.000', kind='link')
    row('shock', 13, 'Extra chance of leaving (layoffs, path)', '%', 'From Scenarios')
    fill('shock', RUN, lambda y: f"=INDEX(Scenarios!{X(y)}${sr['shock']}:{X(y)}${sr['shock'] + 9},MATCH({sc},Scenarios!$B${sr['shock']}:$B${sr['shock'] + 9},0))", fmt=FMT_P, kind='link')
    row('Vraw', 14, 'Company value at Dec 31, before the trim', '$ billions', 'Actual to 2025, then the path')
    fill('Vraw', ALL, lambda y: f'=Data!{X(y)}6*{X(y)}9' if y <= 2025 else f'={P(y)}14*(1+{X(y)}10)', fmt=FMT_BN0)
    row('Yraw', 15, 'Cash paid to owners, before the trim', '$ billions', '2016-2020: dividends + 0.9 x gross buybacks')
    fill('Yraw', ALL, lambda y: (f'=Data!{X(y)}16*{X(y)}9' if y <= 2020 else
                                 (f"=(Data!{X(y)}7+Data!{X(y)}13*(1-{S('haircut')}))*{X(y)}9" if y <= 2025 else f'={X(y)}11*{P(y)}14')), fmt=FMT_BN)
    row('trim', 16, "Profit share's trim on value and cash", '%', 'Smaller if part of the profit share replaces base pay')
    fill('trim', ALL, lambda y: f"={S('trim')}*(1-{S('pay_offset')}*MIN(1,MAX(0,{max(y, 2021)}-2020)/5))", fmt=FMT_P2)
    row('Vreal', 17, 'Value after the trim, 2025 dollars', '$ billions')
    fill('Vreal', ALL, lambda y: f'={X(y)}14*(1-{X(y)}16)*{X(y)}8', fmt=FMT_BN0)
    row('Yreal', 18, 'Cash paid after the trim, 2025 dollars', '$ billions')
    fill('Yreal', ALL, lambda y: f'={X(y)}15*(1-{X(y)}16)*{X(y)}8', fmt=FMT_BN)
    row('Vj', 19, 'Value on Jan 1 (prior Dec 31), after the trim', '$ billions')
    fill('Vj', RUN, lambda y: f'={P(y)}14*(1-{X(y)}16)', fmt=FMT_BN0)
    row('Ve', 20, 'Value on Dec 31, after the trim', '$ billions')
    fill('Ve', RUN, lambda y: f'={X(y)}14*(1-{X(y)}16)', fmt=FMT_BN0)
    row('Yt', 21, 'Cash paid to owners, after the trim', '$ billions')
    fill('Yt', RUN, lambda y: f'={X(y)}15*(1-{X(y)}16)', fmt=FMT_BN)
    row('pop', 22, 'People (July 1)', 'people', 'Census to 2025; CBO growth after')
    fill('pop', range(2020, 2121), lambda y: f'=Data!{X(y)}24' if y <= 2025 else f"={P(y)}22*(1+IF({X(y)}6<=2036,{S('pg1')},{S('pg2')}))", fmt=FMT_N)

    put(ws, 'A24', 'B. Jan 1: new shares', 'h')
    specs = [
        ('cnt_pre', 25, 'Already counted toward the target', 'share'),
        ('filled_prev', 26, 'Target reached before this year? (1 = yes)', 'flag'),
        ('i_pre', 27, 'New shares while filling', 'share'),
        ('wc', 28, 'Worker side counted for top-ups', 'share'),
        ('T', 29, 'Level to restore (citizen + worker at fill)', 'share'),
        ('Pc', 30, 'Held now (citizen + worker side)', 'share'),
        ('i_raw', 31, 'Top-up that restores both', 'share'),
        ('case1', 32, 'Citizen fund needs none (1 = yes)', 'flag'),
        ('case2', 33, 'Workers need none (1 = yes)', 'flag'),
        ('i_post', 34, 'Top-up issue', 'share'),
        ('ac_post', 35, 'Top-up going to the citizen fund', 'share'),
        ('i', 36, 'NEW SHARES ISSUED', 'share of company'),
        ('ac', 37, '  to the citizen fund', 'share'),
        ('aw', 38, '  to the worker trust', 'share'),
        ('c1', 39, 'Citizen fund stake after the issue', 'share'),
        ('give', 40, 'Handed to current workers, equal per worker', 'share'),
        ('q1', 41, 'B: leavers waiting, after the issue', 'share'),
        ('f1', 42, "A: former workers' shares, after the issue", 'share'),
        ('cum1', 43, 'A_forever: former workers\' shares still counted, after the issue', 'share'),
        ('w2', 44, 'Worker trust stake after the issue', 'share'),
        ('cnt_post', 45, 'Counted toward the target after the issue', 'share'),
        ('filled', 46, 'Target reached (1 = yes)', 'flag'),
        ('cstar', 47, 'Citizen level when the target was reached', 'share'),
        ('wstar', 48, 'Worker level when the target was reached', 'share'),
        ('legacy', 49, "Share still held by the people who owned it in 2020", 'share'),
    ]
    for key, r, lab, unit in specs:
        row(key, r, lab, unit)
    put(ws, 'A51', 'C. During the year: workers who leave', 'h')
    specs2 = [
        ('vu', 52, "Vested shares of people who leave", 'share'),
        ('fu', 53, 'Unvested shares forfeited (back to the people still there)', 'share'),
        ('comp_cash', 54, 'C: cash the companies pay leavers', '$ billions'),
        ('Yown', 55, 'Cash paid to owners after any leaver cash', '$ billions'),
        ('tcash', 56, "Worker trust's cash (its share of dividends and buybacks)", '$ billions'),
        ('paid_exit', 57, 'Paid to people who leave', '$ billions'),
        ('passthru', 58, 'Passed to current workers', '$ billions'),
        ('pass_ratio', 59, "Share of the trust's cash passed to current workers", 'share'),
        ('w3', 60, 'Worker trust stake at year end', 'share'),
        ('q3', 61, 'B: leavers still waiting at year end', 'share'),
        ('f3', 62, "A: former workers' shares at year end", 'share'),
        ('cum2', 63, "A_forever: former workers' shares still counted", 'share'),
        ('pool3', 64, 'Shares back in the pool for current workers (handed out Jan 1)', 'share'),
        ('sold_w', 65, 'D/E: trust shares sold to pay leavers', 'share'),
        ('budget', 66, 'B: what the trust can buy back with its cash', 'share'),
        ('spent', 67, 'B: bought back from the queue', 'share'),
        ('dil', 68, 'B: dilution index (for the queue)', 'index'),
        ('CL', 69, 'B: leavers so far, undiluted', 'share'),
        ('CP', 70, 'B: paid so far, undiluted', 'share'),
        ('wait', 71, "B: years the oldest unpaid leaver has waited", 'years'),
    ]
    for key, r, lab, unit in specs2:
        row(key, r, lab, unit)
    put(ws, 'A73', 'D. The citizen fund', 'h')
    specs3 = [
        ('cash_c', 74, 'Cash in (its share of dividends and buybacks)', '$ billions'),
        ('cost', 75, 'Running cost', '$ billions'),
        ('base', 76, 'Payout base', '$ billions'),
        ('check0', 77, 'Check before the limit', '$ billions'),
        ('check', 78, 'Check after the limit', '$ billions'),
        ('gap', 79, 'Left over (+) or short (-)', '$ billions'),
        ('res1', 80, 'Reserve before any bonus', '$ billions'),
        ('sold_c', 81, 'Shares sold to pay checks', '$ billions'),
        ('c_end', 82, 'Citizen fund stake at year end', 'share'),
        ('bonus', 83, 'Bonus from the reserve above its cap', '$ billions'),
        ('reserve', 84, 'Reserve at year end', '$ billions'),
        ('paid', 85, 'Paid out to everyone', '$ billions'),
        ('coverage', 86, 'Cash coverage (cash in / check + cost)', 'x'),
        ('check_pp', 87, 'Ownership dividend per person, as paid', '$'),
        ('fund_pp', 88, 'OWNERSHIP DIVIDEND PER PERSON, 2025 dollars', '$'),
        ('cit_val', 89, 'Citizen fund value at year end', '$ billions'),
        ('wk_val', 90, 'Worker trust value at year end', '$ billions'),
    ]
    for key, r, lab, unit in specs3:
        row(key, r, lab, unit)
    put(ws, 'A92', 'E. Carbon and ads', 'h')
    specs4 = [
        ('fee', 93, 'Carbon fee', '$ per ton'),
        ('tons', 94, 'Emissions with the fee', 'million tons'),
        ('coll', 95, 'Carbon fee collected', '$ billions'),
        ('carb_pp', 96, 'Carbon check per person, as paid', '$'),
        ('gross_pp', 97, 'Gross fee per person, as paid', '$'),
        ('carb_real', 98, 'CARBON CHECK PER PERSON, 2025 dollars', '$'),
        ('gross_real', 99, 'Gross fee per person, 2025 dollars', '$'),
        ('ad_levy', 100, 'Ad levy collected', '$ billions'),
        ('ad_pp', 101, 'Ad check per person, as paid', '$'),
        ('ad_real', 102, 'AD CHECK PER PERSON, 2025 dollars', '$'),
        ('whole', 103, 'WHOLE CHECK PER PERSON, 2025 dollars', '$'),
    ]
    for key, r, lab, unit in specs4:
        row(key, r, lab, unit)
    put(ws, 'A105', 'F. For the stress tests', 'h')
    specs5 = [('fund_yoy', 106, 'Change in the ownership dividend from the year before', '%'),
              ('whole_yoy', 107, 'Change in the whole check from the year before', '%'),
              ('topup_post', 108, 'New shares issued after the target was reached', 'share'),
              ('wk_pay', 109, 'Worker side: paid to leavers plus passed to current workers', '$ billions')]
    for key, r, lab, unit in specs5:
        row(key, r, lab, unit)

    # starting state (2020 column)
    for key, v in [('c_end', 0), ('w3', 0), ('q3', 0), ('f3', 0), ('cum2', 0), ('pool3', 0), ('filled', 0), ('cstar', 0),
                   ('wstar', 0), ('legacy', 1), ('reserve', 0), ('dil', 1), ('CL', 0), ('CP', 0)]:
        put(ws, f'H{MR[key]}', v, 'in', fmt='0.000')
    put(ws, 'H5', 'start', 'note')

    m = lambda k, y: f'{X(y)}{MR[k]}'
    p = lambda k, y: f'{P(y)}{MR[k]}'
    isDE, isAh, isAf, isB, isC, isG = S('isDE'), S('isAh'), S('isAf'), S('isB'), S('isC'), S('isG')
    hasWC = S('hasWC'); tgt = S('tgt'); rate = S('rate'); al = S('alpha_eff')
    F = {}
    F['cnt_pre'] = lambda y: f"={p('c_end',y)}+{p('w3',y)}+{p('q3',y)}+{p('pool3',y)}+{isAh}*{p('f3',y)}+{isAf}*{p('cum2',y)}"
    F['filled_prev'] = lambda y: f"={p('filled',y)}"
    F['i_pre'] = lambda y: f"=IF({m('cnt_pre',y)}<{tgt}-1E-12,MIN({rate},({tgt}-{m('cnt_pre',y)})/(1-{m('cnt_pre',y)})),0)"
    F['wc'] = lambda y: f"=IF({isDE}=1,{p('w3',y)}+{p('q3',y)}+{p('pool3',y)},IF({isAh}=1,{p('w3',y)}+{p('pool3',y)}+{p('f3',y)},0))"
    F['T'] = lambda y: f"={p('cstar',y)}+{p('wstar',y)}"
    F['Pc'] = lambda y: f"={p('c_end',y)}+{m('wc',y)}"
    F['i_raw'] = lambda y: f"=IF({m('Pc',y)}<{m('T',y)}-1E-12,({m('T',y)}-{m('Pc',y)})/(1-{m('Pc',y)}),0)"
    F['case1'] = lambda y: f"=IF(AND({m('i_raw',y)}>0,{p('c_end',y)}*(1-{m('i_raw',y)})>={p('cstar',y)}),1,0)"
    F['case2'] = lambda y: f"=IF(AND({m('i_raw',y)}>0,{m('case1',y)}=0,{m('wc',y)}*(1-{m('i_raw',y)})>={p('wstar',y)}),1,0)"
    F['i_post'] = lambda y: (f"=IF({hasWC}=1,IF({m('i_raw',y)}<=0,0,IF({m('case1',y)}=1,MAX(0,({p('wstar',y)}-{m('wc',y)})/(1-{m('wc',y)})),"
                             f"IF({m('case2',y)}=1,MAX(0,({p('cstar',y)}-{p('c_end',y)})/(1-{p('c_end',y)})),{m('i_raw',y)}))),"
                             f"IF({p('c_end',y)}<{p('cstar',y)}-1E-12,({p('cstar',y)}-{p('c_end',y)})/(1-{p('c_end',y)}),0))")
    F['ac_post'] = lambda y: (f"=IF({hasWC}=1,IF({m('i_raw',y)}<=0,0,IF({m('case1',y)}=1,0,IF({m('case2',y)}=1,{m('i_post',y)},"
                              f"MAX(0,{p('cstar',y)}-{p('c_end',y)}*(1-{m('i_post',y)}))))),{m('i_post',y)})")
    F['i'] = lambda y: f"=IF({m('filled_prev',y)}=1,{m('i_post',y)},{m('i_pre',y)})"
    F['ac'] = lambda y: f"=IF({m('filled_prev',y)}=1,{m('ac_post',y)},(1-{al})*{m('i',y)})"
    F['aw'] = lambda y: f"=IF({m('filled_prev',y)}=1,{m('i',y)}-{m('ac',y)},{al}*{m('i',y)})"
    F['c1'] = lambda y: f"={p('c_end',y)}*(1-{m('i',y)})+{m('ac',y)}"
    F['give'] = lambda y: f"={p('pool3',y)}*(1-{m('i',y)})+{m('aw',y)}"
    F['q1'] = lambda y: f"={p('q3',y)}*(1-{m('i',y)})"
    F['f1'] = lambda y: f"={p('f3',y)}*(1-{m('i',y)})"
    F['cum1'] = lambda y: f"={p('cum2',y)}*(1-{m('i',y)})"
    F['w2'] = lambda y: f"={p('w3',y)}*(1-{m('i',y)})+{m('give',y)}"
    F['cnt_post'] = lambda y: f"={m('c1',y)}+{m('w2',y)}+{m('q1',y)}+{isAh}*{m('f1',y)}+{isAf}*{m('cum1',y)}"
    F['filled'] = lambda y: f"=IF(OR({p('filled',y)}=1,{m('cnt_post',y)}>={tgt}-1E-9),1,0)"
    F['cstar'] = lambda y: f"=IF({p('filled',y)}=1,{p('cstar',y)},IF({m('filled',y)}=1,{m('c1',y)},0))"
    F['wstar'] = lambda y: f"=IF({p('filled',y)}=1,{p('wstar',y)},IF({m('filled',y)}=1,{m('w2',y)}+{m('q1',y)}+{isAh}*{m('f1',y)},0))"
    F['legacy'] = lambda y: f"={p('legacy',y)}*(1-{m('i',y)})"
    wr = WR
    rngs = lambda y: (f"Workers!{X(y)}{wr['n0']}:{X(y)}{wr['n45']}", f"Workers!{X(y)}{wr['h0']}:{X(y)}{wr['h45']}",
                      f"Workers!{X(y)}{wr['u0']}:{X(y)}{wr['u45']}")
    F['vu'] = lambda y: f"=SUMPRODUCT({rngs(y)[0]},{rngs(y)[1]},{rngs(y)[2]},Workers!$C${wr['h0']}:$C${wr['h45']})"
    F['fu'] = lambda y: f"=SUMPRODUCT({rngs(y)[0]},{rngs(y)[1]},{rngs(y)[2]})-{m('vu',y)}"
    F['comp_cash'] = lambda y: f"=IF({isC}=1,{m('vu',y)}*{m('Ve',y)},0)"
    F['Yown'] = lambda y: f"={m('Yt',y)}-{m('comp_cash',y)}"
    F['tcash'] = lambda y: f"=({m('w2',y)}+{m('q1',y)})*{m('Yown',y)}"
    need = lambda y: f"{m('vu',y)}*{m('Ve',y)}"
    use = lambda y: f"MIN({m('tcash',y)},{need(y)})"
    F['paid_exit'] = lambda y: f"=IF({isDE}+{isAh}+{isAf}+{isC}>0,{need(y)},IF({isB}=1,{m('spent',y)}*{m('Ve',y)},0))"
    F['passthru'] = lambda y: (f"=IF({isDE}=1,{m('tcash',y)}-{use(y)},IF({isB}=1,({m('budget',y)}-{m('spent',y)})*{m('Ve',y)},"
                               f"IF({isAh}+{isAf}+{isC}+{isG}>0,{m('tcash',y)},0)))")
    F['pass_ratio'] = lambda y: (f"=IF({isDE}=1,IF({m('tcash',y)}>0,({m('tcash',y)}-{use(y)})/{m('tcash',y)},1),"
                                 f"IF({isB}=1,IF({m('tcash',y)}>0,({m('budget',y)}-{m('spent',y)})*{m('Ve',y)}/{m('tcash',y)},0),1))")
    F['w3'] = lambda y: f"={m('w2',y)}-{m('vu',y)}-{m('fu',y)}"
    F['q3'] = lambda y: f"=IF({isB}=1,{m('q1',y)}+{m('vu',y)}-{m('spent',y)},{m('q1',y)})"
    F['f3'] = lambda y: f"=IF({isAh}+{isAf}>0,({m('f1',y)}+{m('vu',y)})*(1-{S('sale_rate')}),{m('f1',y)})"
    F['cum2'] = lambda y: f"=IF({isAf}=1,{m('cum1',y)}+{m('vu',y)},{m('cum1',y)})"
    F['pool3'] = lambda y: (f"={m('fu',y)}+IF({isDE}=1,{use(y)}/{m('Ve',y)},IF({isB}=1,{m('spent',y)},"
                            f"IF({isC}+{isG}>0,{m('vu',y)},0)))")
    F['sold_w'] = lambda y: f"=IF({isDE}=1,({need(y)}-{use(y)})/{m('Ve',y)},0)"
    F['budget'] = lambda y: f"=IF({isB}=1,{m('tcash',y)}/{m('Ve',y)},0)"
    F['spent'] = lambda y: f"=IF({isB}=1,MIN({m('budget',y)},{m('q1',y)}+{m('vu',y)}),0)"
    F['dil'] = lambda y: f"={p('dil',y)}*(1-{m('i',y)})"
    F['CL'] = lambda y: f"={p('CL',y)}+IF({isB}=1,{m('vu',y)}/{m('dil',y)},0)"
    F['CP'] = lambda y: f"={p('CP',y)}+IF({isB}=1,{m('spent',y)}/{m('dil',y)},0)"
    F['wait'] = lambda y: (f"=IF(AND({isB}=1,{m('q3',y)}>1E-12),{X(y)}6-(2021+IFERROR(MATCH({m('CP',y)}*(1+1E-9),$I${MR['CL']}:{m('CL',y)},1),0))+1,0)")
    F['cash_c'] = lambda y: f"={m('c1',y)}*{m('Yown',y)}"
    F['cost'] = lambda y: f"={S('fund_cost')}*{m('c1',y)}*{m('Vj',y)}"
    F['base'] = lambda y: (f"=IF({S('payout_base')}=\"jan1\",{m('c1',y)}*{m('Vj',y)},IF({S('payout_base')}=\"avg5\","
                           f"{m('c1',y)}*AVERAGE({X(y-5)}{MR['Vreal']}:{X(y-1)}{MR['Vreal']})/{m('dfl',y)},"
                           f"{m('c1',y)}*AVERAGE({X(y-5)}{MR['Yreal']}:{X(y-1)}{MR['Yreal']})/{m('dfl',y)}))")
    F['check0'] = lambda y: f"={S('payout_rate')}*{m('base',y)}"
    F['check'] = lambda y: (f"=IF({S('cash_cap')}=\"cash\",MIN({m('check0',y)},MAX(0,{m('cash_c',y)}-{m('cost',y)})),"
                            f"IF({S('cash_cap')}=\"cash_res\",MIN({m('check0',y)},MAX(0,{m('cash_c',y)}-{m('cost',y)}+{p('reserve',y)})),{m('check0',y)}))")
    F['gap'] = lambda y: f"={m('cash_c',y)}-{m('check',y)}-{m('cost',y)}"
    F['res1'] = lambda y: f"=IF({m('gap',y)}>=0,{p('reserve',y)}+{m('gap',y)},{p('reserve',y)}-MIN({p('reserve',y)},-{m('gap',y)}))"
    F['sold_c'] = lambda y: (f"=IF({m('gap',y)}<0,IF(-{m('gap',y)}-MIN({p('reserve',y)},-{m('gap',y)})>1E-9,"
                             f"-{m('gap',y)}-MIN({p('reserve',y)},-{m('gap',y)}),0),0)")
    F['c_end'] = lambda y: f"=IF(AND({m('sold_c',y)}>0,{m('c1',y)}*{m('Ve',y)}>0),{m('c1',y)}*(1-{m('sold_c',y)}/({m('c1',y)}*{m('Ve',y)})),{m('c1',y)})"
    F['bonus'] = lambda y: (f"=IF(AND({S('capOn')}=1,{m('check',y)}>0,{m('res1',y)}>{S('cap_years')}*{m('check',y)}),"
                            f"({m('res1',y)}-{S('cap_years')}*{m('check',y)})*{S('spread')},0)")
    F['reserve'] = lambda y: f"={m('res1',y)}-{m('bonus',y)}"
    F['paid'] = lambda y: f"={m('check',y)}+{m('bonus',y)}"
    F['coverage'] = lambda y: f"=IF({m('check',y)}+{m('cost',y)}>0,{m('cash_c',y)}/({m('check',y)}+{m('cost',y)}),0)"
    F['check_pp'] = lambda y: f"={m('paid',y)}*1E9/{m('pop',y)}"
    F['fund_pp'] = lambda y: f"={m('check_pp',y)}*{m('dfl',y)}"
    F['cit_val'] = lambda y: f"={m('c_end',y)}*{m('Ve',y)}"
    F['wk_val'] = lambda y: f"=({m('w3',y)}+{m('q3',y)}+{m('pool3',y)})*{m('Ve',y)}"
    # carbon and ads
    on = S('carbOn')
    F['fee'] = lambda y: (f"={S('fee21')}*{on}" if y == 2021 else
                          (f"={S('fee21')}*(1+{S('climb')})^({y}-2021)*Data!{X(y)}25/Data!$I$25*{on}" if y <= 2025 else
                           f"={p('fee',y)}*(1+{S('climb')})"))
    F['tons'] = lambda y: (f"=Data!{X(y)}26*Data!{X(y)}28/Data!{X(y)}27" if y <= 2025 else f"={p('tons',y)}*(1-{S('decline')})")
    F['coll'] = lambda y: f"={m('fee',y)}*{m('tons',y)}/1000"
    F['carb_pp'] = lambda y: f"={m('coll',y)}*(1-{S('collect')})*{S('rebate')}*1E9/{m('pop',y)}"
    F['gross_pp'] = lambda y: f"={m('coll',y)}*1E9/{m('pop',y)}"
    F['carb_real'] = lambda y: f"={m('carb_pp',y)}*{m('dfl',y)}"
    F['gross_real'] = lambda y: f"={m('gross_pp',y)}*{m('dfl',y)}"
    F['ad_levy'] = lambda y: (f"=Data!{X(y)}29*{B.ref('ad_share')}" if y <= 2025 else f"={m('ad_pp',y)}*{m('pop',y)}/1E9")
    F['ad_pp'] = lambda y: (f"={m('ad_levy',y)}*1E9/{m('pop',y)}" if y <= 2025 else f"=$M${MR['ad_pp']}*{S('ad_shrink')}")
    F['ad_real'] = lambda y: f"={m('ad_pp',y)}*{m('dfl',y)}"
    F['whole'] = lambda y: f"={m('fund_pp',y)}+{m('carb_real',y)}+{m('ad_real',y)}"
    F['wk_pay'] = lambda y: f"={m('paid_exit',y)}+{m('passthru',y)}"
    fmts = {'share': '0.0000%', 'flag': '0', '$ billions': FMT_BN, 'share of company': '0.000%', '$': FMT_D, 'x': FMT_X,
            'index': '0.0000', 'years': '0', '$ per ton': '#,##0.00', 'million tons': FMT_BN0, '%': FMT_P2}
    units = {k: u for (k, r, l, u) in specs + specs2 + specs3 + specs4 + specs5}
    for key, fn in F.items():
        fill(key, RUN, fn, fmt=fmts.get(units.get(key, ''), None))
    fill('fund_yoy', range(2026, 2121), lambda y: f"=IF({p('fund_pp',y)}>0,{m('fund_pp',y)}/{p('fund_pp',y)}-1,0)", fmt=FMT_P2)
    fill('whole_yoy', range(2026, 2121), lambda y: f"=IF({p('whole',y)}>0,{m('whole',y)}/{p('whole',y)}-1,0)", fmt=FMT_P2)
    put(ws, 'C3', f"=IFERROR(2020+MATCH(1,$I${MR['filled']}:$DD${MR['filled']},0),9999)", fmt='0', bold=True)
    B.name('fill_year', ws, 'C3')
    fill('topup_post', range(2026, 2121), lambda y: f"=IF({X(y)}6>{B.ref('fill_year')},{m('i',y)},0)", fmt='0.000%')
    ws.column_dimensions['A'].width = 58; ws.column_dimensions['B'].width = 15; ws.column_dimensions['C'].width = 30
    for y in range(2016, 2122):
        ws.column_dimensions[ycol(y)].width = 11
    ws.freeze_panes = 'D5'
    return ws
