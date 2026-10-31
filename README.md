# Everybody Owns a Piece: the model

This is the code behind the numbers in "Everybody Owns a Piece," a plan for giving every American a share of what the country's biggest companies earn. Anyone can run it, check it, change it, and argue with it. That's the point.

## What it does

It runs the whole plan one year at a time, starting in 2021 on real numbers for the 500 biggest U.S. companies, then out to year one hundred:

- companies issue 2.5% of themselves a year into a citizen fund until it holds a quarter
- 10% of pre-tax profit goes to workers, capped at three months' pay each; what the cap clips pays laid-off workers first, then goes to everyone
- the fund pays out cash it actually receives, keeps two years in reserve, and never sells shares to pay a check
- a carbon dividend and an ad-revenue levy go into the same check
- half of most of the money goes into a locked account for a home or retirement
- stress tests: an AI boom, replays of 2000 and 2008, a crash in the plan's third year, fast decarbonization, capital raises, a half stake
- a sample family ("Joe"), and the government's net cost

## How to run it

1. Install Python 3 from python.org.
2. Open a terminal in this folder and run: `pip install numpy`
3. Run `python package.py` for the headline comparison, or `python integrated.py` for everything (it writes integrated_results.json).

## What's measured and what's assumed

Every typed-in number in integrated.py is tagged M (measured, with its source), A (an assumption, tested over a range), or D (a design rule from the plan). The round-two source IDs (S01-S55, R2-01 to R2-41) in engine.py match the sources list in the reports. The three biggest assumptions are pay inside the biggest companies, how fast people take money out of their locked accounts, and how hard companies try to dodge the profit share.

ENGINE_NOTES.md explains the engine files. The build_wb and verify scripts rebuild the round-two spreadsheet and need files that aren't in this folder; you don't need them to run the model.

## License

Public domain (see UNLICENSE). Take it, make it better, make it yours.
