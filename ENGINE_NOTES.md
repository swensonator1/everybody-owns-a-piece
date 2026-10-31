# Engine: Everybody Owns a Piece, integrated run (Oct 31, 2026)

The round-two engine plus the integrated run of essay version 2. Run `python integrated.py` from this folder; it writes integrated_results.json, which the report "Everybody Owns a Piece: The Integrated Run" quotes.

What changed from round two (engine.py): new Design fields trim (0.10 = all ten points leave owners), start_year (plan can start later than 2021), extra_cash (cap overflow into the citizen fund, 2025 $bn), raise_buy; Scenario field raise_ (capital raises, value-neutral). With default settings it reproduces round two exactly.

integrated.py adds: the profit share with its per-person cap (lognormal pay by value-per-employee group), the transition fund (BLS displacement data, five-year benefits, two-year reserve, 2-point backstop), the overflow into the citizen fund, Joe's household with the transition fund, cushion and card payoff, the locked pool and housing guarantee, the government ledger, a recession in the plan's third year, the faster fill, the half stake and capital raises. Every typed-in number is tagged M (measured), A (assumption) or D (design rule).
