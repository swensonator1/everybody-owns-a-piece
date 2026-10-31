import json, time, pickle
import engine as E, score as SC, scenarios as S
t = time.time()
rows = []
for wname, wk in SC.WORKERS.items():
    for pname, pk in SC.PAYOUTS.items():
        d = E.Design(name=f'{wname} | {pname}', **wk, **pk)
        res = SC.evaluate(d, S.all_market() + S.harsher() + [S.reversion_then_crash()])
        p = res['pass']; tt = res['tests']
        rows.append(dict(worker=wname, payout=pname, label=d.payout_label(), **{k: v for k, v in p.items()},
                         **tt, drops={k: (round(v['fund_drop'], 3), v['fund_drop_year']) for k, v in res['by_scen'].items()},
                         sales={k: v['sales_years'] for k, v in res['by_scen'].items()},
                         max_issue={k: round(v['max_issue_post'], 4) for k, v in res['by_scen'].items()}))
print('runs done', round(time.time() - t, 1), 's')
pickle.dump(rows, open('grid.pkl', 'wb'))
for r in rows:
    if r['payout'] in ('P1','P2','P3','P4','P8','P9','P10'): print(f"{r['worker']:30s} {r['payout']:3s} PL1 {int(r['PL1'])} PL2 {int(r['PL2'])} PL3 {int(r['PL3'])} PL4 {int(r['PL4'])} ALL {int(r['all'])} | "
          f"fund2040 {r['fund2040']:6.0f} fund2050 {r['fund2050']:6.0f} legacy50 {r['legacy2050']:.3f} legacy120 {r['legacy2120']:.3f} "
          f"topup {r['topup_lr']*100:.3f}% worstdrop {r['worst_fund_drop']*100:.0f}% wait {r['max_wait']:.0f} fill {r['fill']}")
