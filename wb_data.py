"""Workbook: Data and Sources tabs."""
import numpy as np
from build_wb_part1 import *
import engine as E

HAZ = np.load(os.path.join(HERE, 'hazard.npy'))
DR = {}          # Data rows: key -> row
HIST_ROW = {}    # history table: year -> row


def series(ws, r, label, unit, src, vals, fmt=FMT_BN, kind='in', note=None, key=None):
    put(ws, f'A{r}', label)
    put(ws, f'B{r}', unit)
    put(ws, f'C{r}', src)
    for y, v in vals.items():
        put(ws, f'{ycol(y)}{r}', v, kind if not (isinstance(v, str) and v.startswith('=')) else 'f', fmt=fmt)
    if note:
        put(ws, f'N{r}', note, 'note')
    if key:
        DR[key] = r
    return r


def build_data(B):
    ws = B.wb['Data']
    put(ws, 'A1', 'Measured data', 'title')
    put(ws, 'A2', 'Blue = typed in from the source named in column C (IDs on the Sources tab). Black = calculated here. '
                  'Dollar figures are nominal, as reported. Stock values are at Dec 31.', 'note')
    put(ws, 'A4', 'Item', 'h'); put(ws, 'B4', 'Unit', 'h'); put(ws, 'C4', 'Source', 'h')
    for y in range(2016, 2026):
        put(ws, f'{ycol(y)}4', str(y), 'h')
    put(ws, 'N4', 'Note', 'h')
    ws.column_dimensions['A'].width = 62; ws.column_dimensions['B'].width = 14; ws.column_dimensions['C'].width = 16
    for y in range(2016, 2026):
        ws.column_dimensions[ycol(y)].width = 11
    ws.column_dimensions['N'].width = 70

    put(ws, 'A5', 'S&P 500 (the covered companies in the main run)', 'h')
    series(ws, 6, 'S&P 500 market value at Dec 31', '$ billions', 'R2-01; S03, S04',
           {2016: 18412.04, 2017: 22821.0, 2018: 21027.0, 2019: 26760.0, 2020: 31659, 2021: 40356, 2022: 32133,
            2023: 40039, 2024: 49805, 2025: 58438}, key='mv', note='2025: $58.438 trillion.')
    series(ws, 7, 'S&P 500 cash dividends paid during the year', '$ billions', 'R2-01; S03-S08, S04',
           {2016: 397.21, 2017: 419.77, 2018: 456.31, 2019: 485.48, 2020: 483.18, 2021: 511.23, 2022: 564.57,
            2023: 588.23, 2024: 629.62, 2025: 671.0}, key='div')
    series(ws, 8, 'S&P 500 share buybacks, gross', '$ billions', 'R2-01; S03-S08',
           {2016: 536.38, 2017: 519.4, 2018: 806.41, 2019: 728.74, 2020: 519.76, 2021: 881.72, 2022: 922.68,
            2023: 795.16, 2024: 942.55, 2025: '=M9+M10'}, key='bb',
           note='2025 = Q1-Q3 as published plus a Q4 estimate. S&P DJI never published Q4 2025.')
    series(ws, 9, 'Buybacks, Q1-Q3 2025 only', '$ billions', 'S03', {2025: 777.02}, note='293.45 + 234.57 + 249.00')
    series(ws, 10, 'Q4 2025 buybacks, estimate (set equal to Q3 2025)', '$ billions', 'S03', {2025: 249.0},
           note='Assumption carried from round one.')
    series(ws, 11, "S&P DJI's estimate of the 1% excise tax on net buybacks", '$ billions', 'S03, S05-S08',
           {2021: 7.93, 2022: 8.47, 2023: 7.47, 2024: 8.41}, fmt='0.00',
           note='2021-2022 pro forma (the tax began in 2023). Tax / 1% = net buybacks.')
    series(ws, 12, 'Buyback tax, Q1-Q3 2025 as published plus Q4 estimate (= Q3)', '$ billions', 'S03',
           {2025: '=6.81+2.25'}, fmt='0.00', note='2.43 + 2.13 + 2.25 published; Q4 set equal to Q3 (assumption).')
    series(ws, 13, 'Net buybacks (buybacks minus new shares companies issued)', '$ billions', 'from rows above',
           {**{y: f'={ycol(y)}11/0.01' for y in range(2021, 2025)}, 2025: '=M12/0.01'}, key='netbb')
    series(ws, 14, 'Net buybacks as a share of gross buybacks', '%', 'from rows above',
           {y: f'={ycol(y)}13/{ycol(y)}8' for y in range(2021, 2026)}, fmt=FMT_P)
    put(ws, 'A15', 'Net-to-gross ratio used where net buybacks are not measured (2016-2020 and the replays)')
    put(ws, 'B15', 'ratio'); put(ws, 'C15', 'R2-01')
    put(ws, 'D15', 0.9, 'in', fmt='0.00')
    put(ws, 'N15', 'The 2021-2025 ratios above average 0.91. Assumption, rounded.', 'note')
    B.name('net_ratio', ws, 'D15')
    series(ws, 16, 'Cash paid to owners (dividends plus net buybacks)', '$ billions', 'from rows above',
           {**{y: f'={ycol(y)}7+$D$15*{ycol(y)}8' for y in range(2016, 2021)},
            **{y: f'={ycol(y)}7+{ycol(y)}13' for y in range(2021, 2026)}}, key='cash',
           note='2016-2020 use the ratio in row 15 (used only for the five-year average in the payout rule).')
    put(ws, 'A17', 'Cash yield going forward: (2025 dividends + 2025 net buybacks) / value at end of 2025')
    put(ws, 'B17', 'per year'); put(ws, 'C17', 'from rows above')
    put(ws, 'D17', '=(M7+M13)/M6', fmt=FMT_P2)
    B.name('cy25', ws, 'D17')
    series(ws, 18, 'S&P 500 price return', '%', 'S09',
           {2021: 0.2689, 2022: -0.1944, 2023: 0.2423, 2024: 0.2331, 2025: 0.1639}, fmt=FMT_P2, key='price',
           note='Used only for the index-membership memo on Who paid.')

    put(ws, 'A19', 'All U.S.-listed companies (alternative universe)', 'h')
    series(ws, 20, 'Market value of all U.S.-listed domestic companies (NYSE + Nasdaq)', '$ billions', 'S10',
           {2020: 41569.9, 2021: 48548.5, 2022: 40298, 2023: 48979.4, 2024: 62185.7, 2025: 68937.9}, key='all_listed')
    series(ws, 21, 'All U.S.-listed as a multiple of the S&P 500', 'ratio', 'from rows above',
           {y: f'={ycol(y)}20/{ycol(y)}6' for y in range(2020, 2026)}, fmt='0.000', key='scale',
           note='Used when coverage is set to all U.S.-listed. Years before 2020 use the 2020 ratio.')

    put(ws, 'A23', 'People, prices, emissions, ads, profits', 'h')
    series(ws, 24, 'U.S. resident population, July 1', 'people', 'S01',
           {2020: 331578104, 2021: 332100166, 2022: 333996304, 2023: 336755052, 2024: 340003797, 2025: 341784857},
           fmt=FMT_N, key='pop')
    series(ws, 25, 'Consumer prices (CPI-U, annual average)', 'index', 'S02; R2-02',
           {2016: 240.007, 2017: 245.120, 2018: 251.107, 2019: 255.657, 2020: 258.811, 2021: 270.97, 2022: 292.655,
            2023: 304.702, 2024: 313.689, 2025: 321.943}, fmt='0.000', key='cpi',
           note='2025 is the average of 11 months; October 2025 was never collected (shutdown).')
    series(ws, 26, 'Energy-related CO2 emissions, actual', 'million metric tons', 'S13',
           {2020: 4585.247, 2021: 4905.91, 2022: 4945.217, 2023: 4798.6, 2024: 4789.102, 2025: 4916.398}, key='emis')
    series(ws, 27, 'RFF projection without the fee', 'billion tons', 'S15',
           {2021: 5.1, 2022: 5.0, 2023: 5.0, 2024: 5.0, 2025: 5.0}, fmt='0.0', key='rff_wo')
    series(ws, 28, 'RFF projection with the fee', 'billion tons', 'S15',
           {2021: 4.1, 2022: 4.0, 2023: 3.9, 2024: 3.8, 2025: 3.7}, fmt='0.0', key='rff_w',
           note='The ratio of these two rows is applied to actual emissions.')
    series(ws, 29, 'U.S. internet advertising revenue', '$ billions', 'S17; R2-22',
           {2020: 139.8, 2021: 189.3, 2022: 209.7, 2023: 225.0, 2024: 258.6, 2025: 294.6}, key='ads')
    series(ws, 30, 'Search share of internet ad revenue (2025)', '%', 'R2-22', {2025: 0.388}, fmt=FMT_P, key='search')
    series(ws, 31, 'Domestic corporate profits before tax (all U.S. corporations)', '$ billions', 'S23',
           {2021: 2968.441, 2022: 3158.764, 2023: 3336.995, 2024: 3657.076, 2025: 3655.037}, key='pretax')
    series(ws, 32, 'U.S. GDP', '$ billions', 'S24',
           {2021: 23745.8, 2022: 26059.7, 2023: 27825.9, 2024: 29381, 2025: 30861.3}, key='gdp')

    put(ws, 'A34', 'Who owns U.S. stock (Fed Financial Accounts, Table F.51.1.s, Q4 of each year)', 'h')
    series(ws, 35, 'Public company stock, all domestic issuers (line 58)', '$ billions', 'S11',
           {2020: 47015, 2021: 59448, 2022: 46982, 2023: 57441, 2024: 70648, 2025: 83151}, fmt=FMT_BN0)
    series(ws, 36, 'of which ETF shares (line 16)', '$ billions', 'S11',
           {2020: 5449, 2021: 7191, 2022: 6477, 2023: 8086, 2024: 10305, 2025: 13373}, fmt=FMT_BN0)
    series(ws, 37, 'of which closed-end fund shares (line 15)', '$ billions', 'S11',
           {2020: 279, 2021: 304, 2022: 248, 2023: 250, 2024: 251, 2025: 257}, fmt=FMT_BN0)
    series(ws, 38, 'Public operating-company stock (line 58 minus lines 15 and 16)', '$ billions', 'from rows above',
           {y: f'={ycol(y)}35-{ycol(y)}36-{ycol(y)}37' for y in range(2020, 2026)}, fmt=FMT_BN0)
    series(ws, 39, 'Held by foreign investors (line 57)', '$ billions', 'S11',
           {2020: 10513, 2021: 13698, 2022: 10612, 2023: 13201, 2024: 16663, 2025: 19888}, fmt=FMT_BN0)
    series(ws, 40, "Foreign investors' share of public operating-company stock", '%', 'from rows above',
           {y: f'={ycol(y)}39/{ycol(y)}38' for y in range(2020, 2026)}, fmt=FMT_P, key='foreign',
           note='Upper-end estimate: line 57 may include a little closely held stock and some ETF shares.')

    put(ws, 'A42', 'Wealth groups (Fed Distributional Financial Accounts), Q4 of each year', 'h')
    groups = ['Top 0.1%', 'Next 0.9%', 'Next 9%', 'Next 40%', 'Bottom 50%']
    stock = [[7841.9, 10183, 7797.7, 9466.7, 11504.4, 13773.4], [9436.4, 11249.6, 8708, 10324.7, 12287, 14473.5],
             [12446.6, 15716.9, 12573.4, 14879.2, 17676.6, 20793.8], [3884.1, 4927.5, 4131.3, 4788.8, 5581, 6464.5],
             [192.4, 238.7, 176.8, 216.2, 264.3, 317.8]]
    dc = [[121.4, 126, 97, 116.2, 132.8, 150.6], [961.9, 1125.6, 1001, 1149.7, 1276.9, 1414.5],
          [4228.7, 4738.9, 4101.1, 4715.8, 5242, 5810.8], [3732.1, 4183.5, 3409.7, 4068.5, 4638.7, 5251.1],
          [528.8, 575.3, 468.1, 553, 626.3, 705.1]]
    hh = [[132172, 132774, 133152, 133726, 134624, 136858], [1162444, 1171419, 1182024, 1187122, 1195096, 1214927],
          [11674537, 11754014, 11843333, 11894406, 11974309, 12172999],
          [51887277, 52235735, 52631097, 52858066, 53213150, 54096115],
          [64865613, 65314781, 65823379, 66107239, 66551327, 67655611]]
    yrs = list(range(2020, 2026))
    r = 43
    for g, vals in zip(groups, stock):
        series(ws, r, f'{g}: stock and fund shares held outside DC plans', '$ billions', 'S12', dict(zip(yrs, vals))); r += 1
    series(ws, r, 'All households: stock and fund shares outside DC plans', '$ billions', 'from rows above',
           {y: f'=SUM({ycol(y)}43:{ycol(y)}47)' for y in yrs}); r += 1          # 48
    for g, vals in zip(groups, dc):
        series(ws, r, f'{g}: DC retirement accounts (401k-type)', '$ billions', 'S12', dict(zip(yrs, vals))); r += 1
    series(ws, r, 'All households: DC retirement accounts', '$ billions', 'from rows above',
           {y: f'=SUM({ycol(y)}49:{ycol(y)}53)' for y in yrs}); r += 1          # 54
    for g, vals in zip(groups, hh):
        series(ws, r, f'{g}: households', 'households', 'S12', dict(zip(yrs, vals)), fmt=FMT_N); r += 1
    series(ws, r, 'All households: households', 'households', 'from rows above',
           {y: f'=SUM({ycol(y)}55:{ycol(y)}59)' for y in yrs}, fmt=FMT_N); r += 1   # 60
    DR['stock_share0'] = r
    for i, g in enumerate(groups):
        series(ws, r, f'{g}: share of household stock exposure (stock and funds + DC)', '%', 'from rows above',
               {y: f'=({ycol(y)}{43 + i}+{ycol(y)}{49 + i})/({ycol(y)}48+{ycol(y)}54)' for y in yrs}, fmt=FMT_P2); r += 1
    DR['hh_share0'] = r
    for i, g in enumerate(groups):
        series(ws, r, f'{g}: share of households', '%', 'from rows above',
               {y: f'={ycol(y)}{55 + i}/{ycol(y)}60' for y in yrs}, fmt=FMT_P2); r += 1
    DR['groups'] = groups
    r += 1                                                                    # 72
    put(ws, f'A{r}', "Walmart (Joe's employer; fiscal years mapped to the calendar year they mostly cover)", 'h'); r += 1
    series(ws, r, 'Walmart pre-tax income', '$ millions', 'S19',
           {2021: 18696, 2022: 17016, 2023: 21848, 2024: 26309, 2025: 29469}, fmt=FMT_N, key='wmt_pretax'); r += 1
    series(ws, r, 'Walmart employees (worldwide)', 'people', 'S19',
           {2021: 2234015, 2022: 2204734, 2023: 2149286, 2024: 2165464, 2025: 2100000}, fmt=FMT_N, key='wmt_emp'); r += 1
    series(ws, r, 'Walmart market value at Dec 31', '$ billions', 'S22',
           {2020: 407.84, 2021: 401.35, 2022: 382.38, 2023: 424.43, 2024: 725.82, 2025: 887.96}, fmt='#,##0.00', key='wmt_mv'); r += 1
    series(ws, r, 'Walmart cash paid to owners (dividends plus buybacks)', '$ billions', 'R2-03',
           {2021: 15.939, 2022: 16.034, 2023: 8.919, 2024: 11.182, 2025: 15.595}, fmt='#,##0.000', key='wmt_cash'); r += 1
    put(ws, f'A{r}', "Walmart's 2025 cash yield (cash paid to owners / value at end of 2025)"); put(ws, f'B{r}', 'per year')
    put(ws, f'C{r}', 'from rows above'); put(ws, f'D{r}', f"=M{DR['wmt_cash']}/M{DR['wmt_mv']}", fmt=FMT_P2)
    B.name('wmt_yield', ws, f'D{r}'); r += 2

    put(ws, f'A{r}', "Treasury study of who pays a carbon fee (used for Joe's family)", 'h'); r += 1
    t0 = r
    rows = [('Fee Treasury modeled (2019)', '$ per ton', 'S16', 49, '#,##0'),
            ('Cost to a family at the 40th-50th percentile, before any rebate', '$ per family', 'S16', 630, '#,##0'),
            ("That cost as a share of the family's after-tax income", '%', 'S16', 0.016, FMT_P),
            ('Net gain for that family with a $583-per-person rebate', '% of income', 'S16', 0.012, FMT_P),
            ("Rebate per person in Treasury's run (from its net revenue)", '$ per person', 'S16; R2-04', 583, '#,##0')]
    for lab, un, src, v, fm in rows:
        put(ws, f'A{r}', lab); put(ws, f'B{r}', un); put(ws, f'C{r}', src); put(ws, f'D{r}', v, 'in', fmt=fm); r += 1
    put(ws, f'A{r}', "Derived: that family's after-tax income"); put(ws, f'B{r}', '$'); put(ws, f'D{r}', f'=D{t0+1}/D{t0+2}', fmt='#,##0'); r += 1
    put(ws, f'A{r}', 'Derived: people in that family (rebate received / $583)'); put(ws, f'B{r}', 'people')
    put(ws, f'D{r}', f'=(D{t0+2}+D{t0+3})*D{t0+5}/D{t0+4}', fmt='0.00'); r += 1
    put(ws, f'A{r}', 'Derived: carbon cost per person in that family'); put(ws, f'B{r}', '$ per person')
    put(ws, f'D{r}', f'=D{t0+1}/D{t0+6}', fmt='#,##0.0'); r += 1
    put(ws, f'A{r}', "Derived: middle person's carbon cost / the rebate per person"); put(ws, f'B{r}', 'ratio')
    put(ws, f'D{r}', f'=D{t0+7}/D{t0+4}', fmt='0.000'); B.name('mid_ratio', ws, f'D{r}'); mr = r; r += 1
    put(ws, f'A{r}', 'Share of a carbon fee lost to lower income and payroll taxes (the offset)'); put(ws, f'B{r}', 'share')
    put(ws, f'C{r}', 'R2-04'); put(ws, f'D{r}', 0.25, 'in', fmt=FMT_P); B.name('offset', ws, f'D{r}')
    put(ws, f'N{r}', "Treasury WP-115 p.11; JCT JCX-59-11; CBO 2009. Treasury's $583 rebate came from net revenue, after this offset.", 'note'); off = r; r += 1
    put(ws, f'A{r}', "Middle person's carbon cost as a share of the GROSS fee per person"); put(ws, f'B{r}', 'ratio')
    put(ws, f'C{r}', 'from rows above'); put(ws, f'D{r}', f'=D{mr}*(1-D{off})', fmt='0.000'); B.name('burden_ratio', ws, f'D{r}')
    put(ws, f'N{r}', 'Round one used 0.571 against the gross fee, which overstated the family cost by a third.', 'note'); r += 2

    put(ws, f'A{r}', 'Valuation', 'h'); r += 1
    put(ws, f'A{r}', 'Shiller CAPE (price / 10-year average real earnings), Dec 2025'); put(ws, f'B{r}', 'ratio')
    put(ws, f'C{r}', 'S43'); put(ws, f'D{r}', 39.58, 'in', fmt='0.00'); B.name('cape_now', ws, f'D{r}'); r += 1
    put(ws, f'A{r}', 'Shiller CAPE, long-run average'); put(ws, f'B{r}', 'ratio'); put(ws, f'C{r}', 'S43')
    put(ws, f'D{r}', 17.44, 'in', fmt='0.00'); B.name('cape_avg', ws, f'D{r}'); r += 2

    put(ws, f'A{r}', 'Covered workers', 'h'); r += 1
    put(ws, f'A{r}', 'S&P 500 employees, worldwide, latest annual counts'); put(ws, f'B{r}', 'people'); put(ws, f'C{r}', 'R2-05')
    put(ws, f'D{r}', 29672422, 'in', fmt=FMT_N); B.name('emp_spx', ws, f'D{r}'); r += 1
    put(ws, f'A{r}', 'Job tenure, January 2026: share of workers by years with their current employer (BLS Table 3)', 'h'); r += 1
    bands = [('Under 1 year', 0.206), ('1 to 2 years', 0.063), ('2 to 3 years', 0.058), ('3 to 5 years', 0.201),
             ('5 to 10 years', 0.209), ('10 to 15 years', 0.103), ('15 to 20 years', 0.058), ('20 years or more', 0.102)]
    DR['bls0'] = r
    for lab, v in bands:
        put(ws, f'A{r}', f'   {lab}'); put(ws, f'B{r}', '% of workers'); put(ws, f'C{r}', 'R2-13'); put(ws, f'D{r}', v, 'in', fmt=FMT_P); r += 1
    put(ws, f'A{r}', 'Fitted yearly chance of leaving, by years with the employer', 'h'); r += 1
    put(ws, f'N{r}', 'Fitted in hazard.py so the model\'s steady-state tenure mix matches the BLS shares above (1-5 years pooled because of the 2021-22 hiring wave). Fit check on the Workers tab.', 'note')
    fit = [('First year (tenure 0)', HAZ[0]), ('Years 1-2', HAZ[1]), ('Years 3-9', HAZ[3]), ('Years 10-19', HAZ[10]),
           ('Years 20-44', HAZ[20])]
    DR['haz0'] = r
    for lab, v in fit:
        put(ws, f'A{r}', f'   {lab}'); put(ws, f'B{r}', 'per year'); put(ws, f'C{r}', 'R2-13, fitted')
        put(ws, f'D{r}', float(v), 'in', fmt=FMT_P2); r += 1
    put(ws, f'A{r}', '   Year 45 (everyone has left by then)'); put(ws, f'B{r}', 'per year'); put(ws, f'C{r}', 'model rule')
    put(ws, f'D{r}', 1.0, 'in', fmt=FMT_P); r += 2

    # history for the replays: a vertical table
    put(ws, f'A{r}', 'History for the stress replays: S&P 500, 1999-2013 (vertical table)', 'h'); r += 1
    put(ws, f'A{r}', 'Year', 'h'); put(ws, f'B{r}', 'Price return', 'h'); put(ws, f'C{r}', 'Inflation Dec/Dec', 'h')
    put(ws, f'D{r}', 'Dividends $bn', 'h'); put(ws, f'E{r}', 'Gross buybacks $bn', 'h'); put(ws, f'F{r}', 'Market value $bn', 'h')
    put(ws, f'G{r}', 'Source', 'h'); put(ws, f'H{r}', 'Index level Dec 31', 'h'); r += 1
    import scenarios as S
    for y in range(1999, 2014):
        h = S.HIST[y]
        put(ws, f'A{r}', str(y))
        if y <= 2011:
            put(ws, f'B{r}', h['price'], 'in', fmt=FMT_P2)
        else:
            put(ws, f'B{r}', f'=H{r}/H{r - 1}-1', fmt=FMT_P2)
        if y >= 2011:
            put(ws, f'H{r}', {2011: 1257.60, 2012: 1426.19, 2013: 1848.36}[y], 'in', fmt='#,##0.00')
        put(ws, f'C{r}', S.INFL[y], 'in', fmt=FMT_P2)
        put(ws, f'D{r}', h['div'], 'in', fmt=FMT_BN); put(ws, f'E{r}', h['bb'], 'in', fmt=FMT_BN)
        put(ws, f'F{r}', h['mv'], 'in', fmt=FMT_BN0)
        put(ws, f'G{r}', 'R2-09; R2-02' if y <= 2011 else 'R2-01, R2-10; R2-02')
        HIST_ROW[y] = r
        r += 1
    put(ws, f'A{r}', 'Digitized values (1999-2006) carry chart-reading error of about 1%. 2012-2013 price returns are from Damodaran\'s year-end index levels.', 'note')
    return ws


def build_sources(B):
    ws = B.wb['Sources']
    put(ws, 'A1', 'Sources', 'title')
    put(ws, 'A2', 'Every typed-in number points to one of these IDs. S01-S55 are carried from round one (links checked Oct 18, 2026); R2-01 to R2-41 were added in round two.', 'note')
    for c, h in zip('ABCDEF', ['ID', 'What it supports', 'Source', 'Table or section', 'Link', 'Note']):
        put(ws, f'{c}4', h, 'h')
    rows = load_round_one_sources()
    r = 5
    for row in rows:
        for c, v in zip('ABCDEF', row):
            put(ws, f'{c}{r}', v if v is not None else '', wrap=(c in 'BCDF'))
        r += 1
    for row in SOURCES_R2:
        for c, v in zip('ABCDEF', row):
            put(ws, f'{c}{r}', v, wrap=(c in 'BCDF'))
        r += 1
    for c, w in zip('ABCDEF', [8, 50, 50, 30, 50, 60]):
        ws.column_dimensions[c].width = w
    return ws
