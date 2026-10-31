import json, openpyxl
import verify_wb as V
R = json.load(open('results.json')); FX = json.load(open('fixes_out.json'))
A = V.META['addr']
def val(wbv, key):
    sh, c = V.cell_of(A[key]); return wbv[sh][c].value
def joe_rows(wbv):
    ws = wbv['Joe 40 years']; out = {}
    for r in range(6, 46):
        y = ws[f'A{r}'].value
        out[y] = dict(spendable=ws[f'R{r}'].value, building=ws[f'Y{r}'].value, worker_cash=ws[f'J{r}'].value, worker_stake=ws[f'K{r}'].value,
                      profit_share=ws[f'H{r}'].value, carbon_cost=ws[f'Q{r}'].value, kid_accounts=ws[f'Z{r}'].value)
    return out
def cmp_joe(live, eng):
    e = {x['year']: x for x in eng['rows']}
    worst = {}
    for k in ('spendable', 'building', 'worker_cash', 'worker_stake', 'profit_share', 'carbon_cost', 'kid_accounts'):
        worst[k] = max(abs((live[y][k] or 0) - e[y][k]) for y in range(2021, 2061))
    return worst
# 1. winning setup, split lock
wbv, p = V.run_wb('Winning setup', {}, {'lock': 'split'}, tag='tabs1')
print('Joe (winner, split) worst abs diff:', {k: round(v, 6) for k, v in cmp_joe(joe_rows(wbv), R['joe_win']).items()})
print('  house', val(wbv, 'joe_house'), R['joe_win']['bought'], ' kid1', round(val(wbv, 'joe_kid1'), 2), round(R['joe_win']['kid18']['2018'], 2),
      ' kid2', round(val(wbv, 'joe_kid2'), 2), round(R['joe_win']['kid18']['2021'], 2))
print('  day one', val(wbv, 'd1_drop'), R['day_one']['Winning setup (all to the citizen fund)']['0.0270'], ' per person', val(wbv, 'd1_pp'), R['day_one_recipients']['per_person_citizen'])
g = wbv['Government']
for r in range(5, 17):
    print('  gov', g[f'A{r}'].value, g[f'B{r}'].value, g[f'C{r}'].value)
print('  ledger engine 2025', R['ledger']['2025']); print('  ledger engine 2040', R['ledger']['2040'])
ad = wbv['Ad levy']
for r in range(1, 60):
    a = ad[f'A{r}'].value
    if isinstance(a, str) and (a.startswith('Romer') or a.startswith('Flat') or a.startswith('0/20') or a.startswith('Targeted')):
        if ad[f'B{r}'].value is not None and not isinstance(ad[f'B{r}'].value, str):
            print('  ad', a, round(ad[f'B{r}'].value, 2), round(ad[f'C{r}'].value, 2), round(ad[f'D{r}'].value, 2), round(ad[f'E{r}'].value, 2))
print('  ad engine', {k: (round(v['lo'], 2), round(v.get('mid', v['lo']), 2), round(v['hi'], 2)) for k, v in R['ads_2025'].items()})
# 2. lock variants
for rule in ('half', 'quarter', 'none'):
    wbv2, p2 = V.run_wb('Winning setup', {}, {'lock': rule}, tag='tabs_' + rule)
    lv = joe_rows(wbv2)
    e = R['lock'][rule]
    print(f'  lock {rule}: spend2025 {lv[2025]["spendable"]:.2f} vs {e["spend2025"]:.2f}; build2060 {lv[2060]["building"]:.2f} vs {e["build2060"]:.2f}; house', val(wbv2, 'joe_house'), e['bought'])
# 3. essay as written, half lock
wbv3, p3 = V.run_wb('Essay as written', {}, {'lock': 'half'}, tag='tabs3')
print('Joe (essay, half) worst abs diff:', {k: round(v, 6) for k, v in cmp_joe(joe_rows(wbv3), R['joe_essay']).items()})
print('  day one essay with turnover', val(wbv3, 'd1_drop'), R['day_one']['Essay as written, real turnover']['0.0270'])
# 4. round one: who paid
wbv4, p4 = V.run_wb('Round one bookkeeping', {}, {}, tag='tabs4')
print('Who paid: net', val(wbv4, 'wp_net'), FX['net_transfer_total'], ' self', val(wbv4, 'wp_self'), FX['self_dilution_total'],
      ' memo', val(wbv4, 'wp_memo'), ' new', val(wbv4, 'wp_new'), FX['new_shares_total'], ' worker cash', val(wbv4, 'wp_wcash'), FX['worker_trust_cash_2021_2025'])
wp = wbv4['Who paid']
for r in range(5, 50):
    a = wp[f'A{r}'].value
    if a and wp[f'H{r}'].value is not None:
        print('   ', a[:70], round(wp[f'H{r}'].value, 2) if isinstance(wp[f'H{r}'].value, float) else wp[f'H{r}'].value)
print('  engine groups', {k: round(v, 2) for k, v in FX['given_up_by_group'].items()})
print('  engine citizen net by group', {k: round(v, 2) for k, v in FX['citizen_half_net_gain_by_group'].items()})
print('  day one round one', val(wbv4, 'd1_drop'), R['day_one']['Essay as written, nobody leaves']['0.0270'])
# 5. G and A_forever Joe
for code, key in (('G', 'joe_G'), ('A_forever', 'joe_A_forever')):
    import engine as E
    d = E.Design(worker=code, payout_rate=0.80, payout_base='cash_avg5', cash_cap='cash_res', bonus_spread=0.2)
    wbv5, p5 = V.run_wb('Custom', {'worker': code}, {'lock': 'split'}, tag='tabs_' + code)
    print(f'Joe ({code}, split) worst abs diff:', {k: round(v, 6) for k, v in cmp_joe(joe_rows(wbv5), R[key]).items()})
