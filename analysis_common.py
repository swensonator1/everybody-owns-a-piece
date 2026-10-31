import engine as E, scenarios as S, score as SC
P10 = dict(payout_rate=0.80, payout_base='cash_avg5', cash_cap='cash_res', bonus_spread=0.2)
scen_all = S.all_market() + S.harsher() + [S.reversion_then_crash()]
def real(series, y):
    return series[y] * E.to2025(y)
