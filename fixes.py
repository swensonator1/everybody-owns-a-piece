"""Round-two fixes measured on round one's own settings (essay as written: nobody leaves, 3% of Jan 1 value)."""
import engine as E, json
r1 = E.Design(name='round1', worker='D', turnover_scale=0.0, reserve_cap_years=None)
r = E.run(r1, end=2040)
out = {}
# F1: who paid, net of the trusts' own dilution
new_sh = {}; self_dil = {}; net = {}
prev_stake = 0.0
for y in range(2021, 2026):
    i = r['issue'][y]; Vj = r['Vjan'][y]
    new_sh[y] = i * Vj; self_dil[y] = i * prev_stake * Vj; net[y] = new_sh[y] - self_dil[y]
    prev_stake = r['c'][y] + r['w'][y]
out['new_shares_total'] = sum(new_sh.values()); out['self_dilution_total'] = sum(self_dil.values())
out['net_transfer_total'] = sum(net.values()); out['index_reclass_total'] = sum(E.__dict__.get('INDEX_RECLASS', {}).values()) if hasattr(E, 'INDEX_RECLASS') else None
# groups: foreign share at Jan 1 of each year (prior Q4), wealth groups' stock exposure at prior Q4
FS = E.FOREIGN_SHARE
import importlib
grp = {k: 0.0 for k in ['Foreign investors', 'Top 0.1%', 'Next 0.9%', 'Next 9%', 'Next 40%', 'Bottom 50%']}
STOCK = {2020: [0.183594893750447, 0.239734128274116, 0.384451161171477, 0.175592459129023, 0.0166273576749365],
         2021: [0.19427117685857, 0.233208329407331, 0.385485725054179, 0.171695090926223, 0.0153396777536983],
         2022: [0.185914690291328, 0.22864019253911, 0.39267286955334, 0.177585301466415, 0.0151869461498065],
         2023: [0.190595240936538, 0.22821547053629, 0.389726882900944, 0.176163711146646, 0.0152986944795819],
         2024: [0.19647475941246, 0.229003883167314, 0.386942427823738, 0.172542630423772, 0.0150362991727165]}
HH = {2020: [0.00101888620425135, 0.00896103679156518, 0.0899965551729709, 0.399988126921498, 0.500035394909715],
      2021: [0.00101657834905866, 0.00896891856143483, 0.089994096336123, 0.399940630305374, 0.50007977644801],
      2022: [0.00101169348905809, 0.008981059125739, 0.0899860526679795, 0.399892890507726, 0.500128304209497],
      2023: [0.0010116918933593, 0.0089810635465689, 0.0899860470403972, 0.399892891964544, 0.500128305555131],
      2024: [0.00101168942258959, 0.00898105822274731, 0.0899860482389424, 0.399892894266056, 0.500128309849665]}
names = ['Top 0.1%', 'Next 0.9%', 'Next 9%', 'Next 40%', 'Bottom 50%']
cit_net = {n: 0.0 for n in names}
cprev = 0.0
for y in range(2021, 2026):
    fs = FS[y - 1]
    grp['Foreign investors'] += net[y] * fs
    for n, s in zip(names, STOCK[y - 1]):
        grp[n] += net[y] * (1 - fs) * s
    # citizen half's own net gain from the issue: half the new shares less its own dilution
    i = r['issue'][y]; Vj = r['Vjan'][y]
    gain = (0.5 * i - i * cprev) * Vj
    for n, h in zip(names, HH[y - 1]):
        cit_net[n] += gain * h
    cprev = r['c'][y]
out['given_up_by_group'] = grp
out['citizen_half_net_gain_by_group'] = cit_net
out['citizen_half_net_gain_total'] = sum(cit_net.values())
out['worker_half_net_gain_total'] = out['net_transfer_total'] - out['citizen_half_net_gain_total']
# F3: worker trust cash 2021-2025 (round one: passed to workers or used for leavers) = trust share of payouts
wc = sum(r['w'][y - 1 if y > 2021 else y] * 0 for y in range(2021, 2026))
out['worker_trust_cash_2021_2025'] = sum((r['issue'][y] * 0) for y in range(2021, 2026))
# recompute directly: worker stake after the issue x payouts
wstake = {}; prev = 0.0
for y in range(2021, 2026):
    i = r['issue'][y]; wstake[y] = prev * (1 - i) + 0.5 * i; prev = r['w'][y]
out['worker_trust_cash_by_year'] = {y: wstake[y] * r['payouts'][y] for y in range(2021, 2026)}
out['worker_trust_cash_2021_2025'] = sum(out['worker_trust_cash_by_year'].values())
# F4: coverage under central estimates and with net buybacks 10% lower, or running costs at 0.2%
out['coverage_central'] = {y: r['coverage'][y] for y in range(2021, 2026)}
r10 = E.run(E.Design(worker='D', turnover_scale=0.0, reserve_cap_years=None, netbb_haircut=0.10), end=2026)
out['coverage_netbb_minus10'] = {y: r10['coverage'][y] for y in range(2021, 2026)}
out['reserve_netbb_minus10'] = {y: r10['reserve'][y] for y in range(2021, 2026)}
out['sold_netbb_minus10'] = {y: r10['sold_c'][y] for y in range(2021, 2026)}
rc = E.run(E.Design(worker='D', turnover_scale=0.0, reserve_cap_years=None, fund_cost=0.002), end=2026)
out['coverage_cost02'] = {y: rc['coverage'][y] for y in range(2021, 2026)}
out['reserve_cost02'] = {y: rc['reserve'][y] for y in range(2021, 2026)}
out['sold_cost02'] = {y: rc['sold_c'][y] for y in range(2021, 2026)}
rb = E.run(E.Design(worker='D', turnover_scale=0.0, reserve_cap_years=None, fund_cost=0.002, netbb_haircut=0.10), end=2026)
out['coverage_both'] = {y: rb['coverage'][y] for y in range(2021, 2026)}
out['reserve_both'] = {y: rb['reserve'][y] for y in range(2021, 2026)}
out['sold_both'] = {y: rb['sold_c'][y] for y in range(2021, 2026)}
out['reserve_central'] = {y: r['reserve'][y] for y in range(2021, 2026)}
json.dump(out, open('fixes_out.json', 'w'), indent=1, default=float)
for k, v in out.items():
    print(k, v if not isinstance(v, dict) else {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()})
