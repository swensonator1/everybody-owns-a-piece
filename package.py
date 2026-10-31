"""The recommended package vs the essay as written (Oct 31, 2026). Run: python package.py"""
import engine as E, scenarios as S, integrated as I
P10 = I.P10
PACKAGES = [('Earlier design: quarter at 1.5%', {}),
            ('This plan: quarter at 2.5%, 60% payout while filling', dict(issue_rate=0.025, fill_payout_rate=0.6)),
            ('Stage two: half at 3%, 60% payout while filling', dict(target=0.5, issue_rate=0.03, fill_payout_rate=0.6))]
for nm, kw in PACKAGES:
    d = E.Design(worker='F', trim=0.10, **P10, **kw)
    c = I.run_all('c', E.Scenario(), d); b = I.run_all('b', S.ai_boom(), d, boom=True)
    d26 = E.Design(**{**d.__dict__, 'start_year': 2026})
    rec = I.run_all('rec', I.make_recession_y3(), d26); m = I.run_all('m', S.replay_2008(), d)
    w = lambda r, y: round(I.whole_pp(r, y))
    fd = I.worst_drop(rec['r']['check_pp_real'], range(2027, 2041))[0]
    wd = I.worst_drop({y: I.whole_pp(rec['r'], y) for y in range(2026, 2041)}, range(2027, 2041))[0]
    md = I.worst_drop({y: I.whole_pp(m['r'], y) for y in range(2044, 2056)}, range(2045, 2056))[0]
    mf = I.worst_drop(m['r']['check_pp_real'], range(2045, 2056))[0]
    print(f"{nm}\n  full in {c['r']['fill_year']}; whole check per person yr5 {w(c['r'],2025)}, yr10 {w(c['r'],2030)}, yr20 {w(c['r'],2040)}, yr30 {w(c['r'],2050)}; "
          f"boom yr10 {w(b['r'],2030)}, yr30 {w(b['r'],2050)}\n  year-3 crash: fund -{fd:.0%}, whole -{wd:.0%}; full-fund crash: fund -{mf:.0%}, whole -{md:.0%}; owners keep {c['r']['legacy'][2120]:.0%}")
