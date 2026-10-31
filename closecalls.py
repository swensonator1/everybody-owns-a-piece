"""Close calls around the winner, plus the cash-pipe stress tests (fast decarbonization, smaller ad base)."""
import json
import engine as E, scenarios as S, score as SC
from analysis_common import *
out = {}
variants = {
    'Winner (80% of 5-yr avg cash, 2-yr reserve cap, a fifth of the excess a year)': dict(**P10),
    '75% of 5-yr avg cash': dict(P10, payout_rate=0.75),
    '85% of 5-yr avg cash': dict(P10, payout_rate=0.85),
    '90% of 5-yr avg cash': dict(P10, payout_rate=0.90),
    '80%, 3-year reserve cap': dict(P10, reserve_cap_years=3.0),
    '80%, 1-year reserve cap': dict(P10, reserve_cap_years=1.0),
    '80%, excess paid all at once': dict(P10, bonus_spread=1.0),
    '80%, a tenth of the excess a year': dict(P10, bonus_spread=0.1),
    '80% of last year\'s cash (no averaging)': None,
    'P9: 2.5% of 5-yr avg value, cash+reserve limit, a fifth a year': SC.PAYOUTS['P9'],
}
for nm, kw in variants.items():
    if kw is None:
        continue
    d = E.Design(worker='F', **kw)
    res = SC.evaluate(d, scen_all)
    cr = res['by_scen'][scen_all[0].name]['r']
    out[nm] = dict(pass_=res['pass'], fund2026=cr['check_pp_real'][2026], fund2030=cr['check_pp_real'][2030],
                   fund2040=cr['check_pp_real'][2040], fund2050=cr['check_pp_real'][2050],
                   reserve2050=cr['reserve'][2050],
                   drops={k: round(v['fund_drop'], 4) for k, v in res['by_scen'].items()},
                   whole={k: round(v['whole_drop'], 4) for k, v in res['by_scen'].items()},
                   worst=max(v['fund_drop'] for v in res['by_scen'].values()),
                   worst_whole=max(v['whole_drop'] for v in res['by_scen'].values()),
                   sales=sum(v['sales_years'] for v in res['by_scen'].values()),
                   total_paid_2026_2060=sum(cr['check'][y] for y in range(2026, 2061)))
# cash pipes: winner under fast decarbonization and a smaller ad base (whole-check falls)
win = E.Design(worker='F', **P10)
rw = E.run(win)
def worst(series, years):
    w = 0.0; wy = None
    for y in years:
        ch = series[y] / series[y - 1] - 1
        if ch < w:
            w, wy = ch, y
    return -w, wy
pipes = {}
for nm, cb, ad in [('central', E.carbon_path(), E.ad_path()),
                   ('fast decarbonization (7.5% a year)', E.carbon_path(decline=lambda y: 0.075 if y >= 2026 else 0.025), E.ad_path()),
                   ('smaller ad base (25% lower from 2026)', E.carbon_path(), E.ad_path(shrink=lambda y: 0.75 if y >= 2026 else 1.0)),
                   ('no carbon', E.carbon_path(on=False), E.ad_path()),
                   ('75% carbon rebate', E.carbon_path(rebate_share=0.75), E.ad_path())]:
    whole = {y: rw['check_pp_real'][y] + real(cb['check_pp'], y) + real(ad['check_pp'], y) for y in range(2021, 2121)}
    wd, wy = worst(whole, range(2026, 2121))
    pipes[nm] = dict(worst_whole=wd, worst_year=wy, whole2025=whole[2025], whole2030=whole[2030], whole2040=whole[2040],
                     whole2050=whole[2050], whole2070=whole[2070], carbon2040=real(cb['check_pp'], 2040),
                     carbon2050=real(cb['check_pp'], 2050), carbon2070=real(cb['check_pp'], 2070),
                     ads2040=real(ad['check_pp'], 2040),
                     first_year_fund_above_carbon=next((y for y in range(2021, 2121) if rw['check_pp_real'][y] > real(cb['check_pp'], y)), None))
    # also with the carbon line peaking: carbon collected peaks when fee growth = decline
    pipes[nm]['carbon_peak_year'] = max(range(2021, 2121), key=lambda y: real(cb['check_pp'], y))
out['pipes'] = pipes
# repeal of carbon in 2040 (a political event, shown separately)
json.dump(out, open('closecalls.json', 'w'), indent=1, default=float)
for k, v in out.items():
    if k == 'pipes':
        for kk, vv in v.items():
            print(kk, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in vv.items()})
    else:
        print(k, v['pass_'], 'f26', round(v['fund2026']), 'f30', round(v['fund2030']), 'f40', round(v['fund2040']), 'f50', round(v['fund2050']), 'worst', round(v['worst'], 3), 'whole', round(v['worst_whole'], 3), 'sales', v['sales'])
        print('    drops', v['drops'])
