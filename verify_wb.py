"""Set switches in the workbook, recalculate with LibreOffice, and compare the live Model with the engine."""
import json, os, subprocess, sys, shutil
import openpyxl
from openpyxl.utils import get_column_letter
import engine as E, scenarios as S, family as FAM

RECALC = '/root/.claude/skills/synced/7553cdb7-9bbd-4aa9-adb3-1184333161d5_f1adfdf9-92c8-491d-ad02-bd346b0b4d9f/xlsx/scripts/recalc.py'
BASE = sys.argv[1] if len(sys.argv) > 1 else '../../out/wb_test.xlsx'
META = json.load(open(BASE + '.addr.json'))
MR, SW = META['MR'], META['SW']
ycol = lambda y: get_column_letter(4 + (y - 2016))
P10 = dict(payout_rate=0.80, payout_base='cash_avg5', cash_cap='cash_res', bonus_spread=0.2)

def cell_of(ref):
    sheet, c = ref.split('!')
    return sheet.strip("'"), c.replace('$', '')

SWROW = {}
wb0 = openpyxl.load_workbook(BASE)
ws0 = wb0['Switches']
for k, ref in SW.items():
    sh, c = cell_of(ref)
    SWROW[k] = c

def run_wb(preset, custom=None, other=None, tag='t'):
    wb = openpyxl.load_workbook(BASE)
    ws = wb['Switches']
    ws[SWROW['preset']] = preset
    for k, v in (custom or {}).items():
        row = ''.join(ch for ch in SWROW[k] if ch.isdigit())
        ws[f'G{row}'] = v
    for k, v in (other or {}).items():
        ws[SWROW[k]] = v
    out = BASE.replace('.xlsx', f'_{tag}.xlsx')
    wb.save(out)
    res = subprocess.run(['python3', RECALC, out, '300'], capture_output=True, text=True)
    info = json.loads(res.stdout)
    assert info.get('status') == 'success', info
    return openpyxl.load_workbook(out, data_only=True), out

def model_series(wbv, key, y0=2021, y1=2120):
    ws = wbv['Model']
    return {y: ws[f'{ycol(y)}{MR[key]}'].value for y in range(y0, y1 + 1)}

def compare(wbv, r, name):
    pairs = [('fund_pp', 'check_pp_real'), ('legacy', 'legacy'), ('c_end', 'c'), ('reserve', 'reserve'), ('paid', 'check'),
             ('i', 'issue'), ('wk_val', 'worker_val'), ('cit_val', 'citizen_val')]
    out = {}
    for mk, ek in pairs:
        live = model_series(wbv, mk)
        diffs = [abs((live[y] or 0) - r[ek][y]) for y in range(2021, 2121)]
        rel = [abs((live[y] or 0) - r[ek][y]) / max(1e-12, abs(r[ek][y])) for y in range(2021, 2121) if abs(r[ek][y]) > 1e-9]
        out[mk] = (max(diffs), max(rel) if rel else 0.0)
    wait = model_series(wbv, 'wait'); ew = r['max_wait']
    out['max_wait'] = (max(wait.values()), max(ew.values()))
    return out

if __name__ == '__main__':
    cases = [
        ('Winning setup', None, None, E.Design(worker='F', **P10), None),
        ('Essay as written', None, None, E.Design(worker='D'), None),
        ('Round one bookkeeping', None, None, E.Design(worker='D', turnover_scale=0.0, reserve_cap_years=None), None),
    ]
    results = []
    for preset, cu, ot, d, sc in cases:
        wbv, path = run_wb(preset, cu, ot, tag=preset.split()[0].lower())
        r = E.run(d, sc)
        cmp = compare(wbv, r, preset)
        print(preset, {k: (round(v[0], 6), round(v[1], 8)) if isinstance(v[0], float) else v for k, v in cmp.items()})

def full_suite():
    import scenarios as S
    scen = S.all_market() + S.harsher() + [S.reversion_then_crash()]
    names = [s.name for s in scen]
    P1 = dict(payout_rate=0.03, payout_base='jan1', cash_cap='none', bonus_spread=1.0)
    P9 = dict(payout_rate=0.025, payout_base='avg5', cash_cap='cash_res', bonus_spread=0.2)
    def cust(d):
        m = dict(worker=d.worker, alpha=d.alpha, vesting=d.vesting, turnover=d.turnover_scale, retention=d.retention,
                 sale_rate=d.sale_rate, payout_rate=d.payout_rate, payout_base=d.payout_base, cash_cap=d.cash_cap,
                 cap_on='Yes' if d.reserve_cap_years is not None else 'No', cap_years=d.reserve_cap_years or 2,
                 spread=d.bonus_spread, issue_rate=d.issue_rate, target=d.target, us_share=d.us_share,
                 coverage='All U.S.-listed' if d.coverage == 'all_listed' else 'S&P 500', pay_offset=d.pay_offset,
                 fund_cost=d.fund_cost, haircut=d.netbb_haircut)
        return m
    cases = []
    cases.append(('Round one bookkeeping (preset)', 'Round one bookkeeping', {}, E.Design(worker='D', turnover_scale=0.0, reserve_cap_years=None), scen[0]))
    designs = [
        ('D, 3% of Jan 1 value, 20% of new shares to workers', E.Design(worker='D', alpha=0.2, **P1)),
        ('D, three-year vesting, cash rule', E.Design(worker='D', vesting=3, **P10)),
        ('A_hold, cash rule', E.Design(worker='A_hold', **P10)),
        ('A_forever, cash rule', E.Design(worker='A_forever', **P10)),
        ('B, cash rule', E.Design(worker='B', **P10)),
        ('C, cash rule', E.Design(worker='C', **P10)),
        ('E (10% land at covered firms), cash rule', E.Design(worker='E', **P10)),
        ('E (30%), 2.5% of 5-yr avg value', E.Design(worker='E', retention=0.30, **P9)),
        ('G, cash rule', E.Design(worker='G', **P10)),
        ('F, 3% of Jan 1 value', E.Design(worker='F', **P1)),
        ('F, all U.S.-listed', E.Design(worker='F', coverage='all_listed', **P10)),
        ('F, issue and target x 71% U.S. share', E.Design(worker='F', us_share=0.71, **P10)),
        ('F, half the profit share out of base pay', E.Design(worker='F', pay_offset=0.5, **P10)),
        ('Round one with net buybacks 10% lower and 0.2% costs', E.Design(worker='D', turnover_scale=0.0, reserve_cap_years=None, netbb_haircut=0.10, fund_cost=0.002)),
    ]
    for nm, d in designs:
        cases.append((nm, 'Custom', cust(d), d, scen[0]))
    win = E.Design(worker='F', **P10)
    for sc in scen[1:]:
        cases.append((f'Winning setup on: {sc.name}', 'Winning setup', {}, win, sc))
    dD = E.Design(worker='D', **P10)
    for i in (3, 4):
        cases.append((f'D, cash rule, on: {scen[i].name}', 'Custom', cust(dD), dD, scen[i]))
    dB = E.Design(worker='B', **P10)
    cases.append((f'B, cash rule, on: {scen[3].name}', 'Custom', cust(dB), dB, scen[3]))
    out = []
    for k, (nm, preset, cu, d, sc) in enumerate(cases):
        other = {'scenario': sc.name}
        wbv, path = run_wb(preset, cu, other, tag=f'v{k}')
        r = E.run(d, sc)
        cmp = compare(wbv, r, nm)
        ok = (cmp['fund_pp'][0] < 1e-6 and cmp['legacy'][0] < 1e-9 and cmp['c_end'][0] < 1e-9 and cmp['reserve'][1] < 1e-6
              and cmp['max_wait'][0] == cmp['max_wait'][1])
        out.append(dict(name=nm, fund=cmp['fund_pp'][0], legacy=cmp['legacy'][0], c=cmp['c_end'][0],
                        result='Matches' if ok else 'Differs', detail={kk: vv for kk, vv in cmp.items()}))
        print(('OK  ' if ok else 'DIFF'), nm, {kk: (vv[0] if isinstance(vv[0], int) else round(vv[0], 8), vv[1] if isinstance(vv[1], int) else round(vv[1], 9)) for kk, vv in cmp.items()})
        os.remove(path)
    return out
