"""Workbook builder, part 1: styles, helpers, Data, Sources, Switches, Scenarios."""
import json, csv, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.comments import Comment

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', '..', 'research')
ARIAL = 'Arial'
F_TITLE = Font(name=ARIAL, size=14, bold=True)
F_H = Font(name=ARIAL, size=11, bold=True)
F_B = Font(name=ARIAL, size=10)
F_BB = Font(name=ARIAL, size=10, bold=True)
F_IN = Font(name=ARIAL, size=10, color='0000FF')          # typed in from a source
F_LINK = Font(name=ARIAL, size=10, color='008000')        # pulled from another tab
F_NOTE = Font(name=ARIAL, size=9, italic=True, color='555555')
YELLOW = PatternFill('solid', fgColor='FFFF00')
GREY = PatternFill('solid', fgColor='EFEFEF')
GREEN_F = PatternFill('solid', fgColor='E2F0D9')
RED_F = PatternFill('solid', fgColor='FBE2E2')
WRAP = Alignment(wrap_text=True, vertical='top')
Y0, Y1 = 2016, 2120


def ycol(y):
    """Year columns are shared by Data, Scenarios, Model, Joe and Day one: 2016 = D ... 2120 = DD."""
    return get_column_letter(4 + (y - Y0))


class Book:
    def __init__(self):
        self.wb = Workbook()
        self.wb.remove(self.wb.active)
        self.addr = {}

    def sheet(self, name):
        ws = self.wb.create_sheet(name)
        ws.sheet_view.showGridLines = True
        return ws

    def name(self, key, ws, cell, absolute=True):
        col = ''.join(ch for ch in cell if ch.isalpha()); row = ''.join(ch for ch in cell if ch.isdigit())
        ref = f"${col}${row}" if absolute else cell
        sheet = ws.title
        q = f"'{sheet}'" if ' ' in sheet or '-' in sheet else sheet
        self.addr[key] = f"{q}!{ref}"
        return self.addr[key]

    def ref(self, key):
        return self.addr[key]


def put(ws, cell, value, kind='f', fmt=None, bold=False, fill=None, note=None, wrap=False):
    c = ws[cell]
    c.value = value
    if kind == 'in':
        c.font = Font(name=ARIAL, size=10, color='0000FF', bold=bold)
    elif kind == 'link':
        c.font = Font(name=ARIAL, size=10, color='008000', bold=bold)
    elif kind == 'h':
        c.font = F_H
    elif kind == 'title':
        c.font = F_TITLE
    elif kind == 'note':
        c.font = F_NOTE
    else:
        c.font = Font(name=ARIAL, size=10, bold=bold)
    if fmt:
        c.number_format = fmt
    if fill is not None:
        c.fill = fill
    if note:
        c.comment = Comment(note, 'round two')
    if wrap:
        c.alignment = WRAP
    return c


FMT_BN = '#,##0.0;(#,##0.0);-'
FMT_BN0 = '#,##0;(#,##0);-'
FMT_D = '$#,##0;($#,##0);-'
FMT_P = '0.0%;(0.0%);-'
FMT_P2 = '0.00%;(0.00%);-'
FMT_X = '0.00"x"'
FMT_N = '#,##0'

# ------------------------------------------------------------------------------------------------ sources
SOURCES_R1 = []   # filled from round one's workbook
def load_round_one_sources():
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(HERE, '..', 'Everybody_Owns_a_Piece_Backtest.xlsx'), data_only=True)
    ws = wb['Sources']
    rows = []
    for r in ws.iter_rows(min_row=5, values_only=True):
        if r[0]:
            rows.append(list(r[:6]))
    return rows

SOURCES_R2 = [
 ('R2-01', 'S&P 500 market value, dividends and gross buybacks 2012-2024 (and 2016-2020 used for five-year averages)',
  'S&P Dow Jones Indices buyback press releases, annual tables', 'Releases of Mar 22, 2017; Mar 15, 2022; Dec 18, 2025',
  'https://press.spglobal.com/2017-03-22-S-P-500-Buybacks-Total-135-3-Billion-for-Q4-2016-Decline-for-Full-Year-2016 ; https://press.spglobal.com/2022-03-15-S-P-500-Buybacks-Set-Quarterly-and-Annual-Record',
  'Net buybacks before 2021 are not measured; 0.9 of gross (the 2021-2025 measured ratio) is used for the five-year cash average.'),
 ('R2-02', 'CPI-U annual averages 1995-2016; December-to-December inflation 1997-2013', 'BLS via FRED (CPIAUCNS); Damodaran histretSP.xls', 'Annual average; Dec/Dec column',
  'https://fred.stlouisfed.org/series/CPIAUCNS ; https://pages.stern.nyu.edu/~adamodar/pc/datasets/histretSP.xls', ''),
 ('R2-03', "Cash paid to owners (dividends + share repurchases) by Walmart, Amazon, Target, Costco, Kroger, Home Depot, Apple, Nvidia",
  'Company 10-K cash flow statements on SEC EDGAR, cross-matched to XBRL companyfacts', 'Financing activities; fiscal years mapped to the calendar year they mostly cover',
  'https://www.sec.gov/Archives/edgar/data/104169/000010416926000055/wmt-20260131.htm (Walmart; others in the research file)', 'Walmart: about 1.6 million U.S. associates of 2.1 million (Jan 31, 2026).'),
 ('R2-04', 'The 25 percent offset: an excise tax shrinks the income and payroll tax base; Treasury rebate of $583 per person came from net revenue',
  'U.S. Treasury OTA Working Paper 115 (Horowitz et al., Jan 2017); JCT JCX-59-11 (Dec 23, 2011); CBO (Jan 13, 2009); JCT JCX-10-25 (Feb 2025)',
  'WP-115 p.3, p.11, Table 2, Table 5 totals ($194.3B = net revenue); JCX-59-11 p.1 and p.5; JCX-10-25: 0.244 for 2025',
  'https://home.treasury.gov/system/files/131/WP-115.pdf ; https://www.jct.gov/getattachment/fe1ce409-c05f-4f1d-8c92-93496125f340/x-59-11-4378.pdf ; https://www.cbo.gov/sites/default/files/111th-congress-2009-2010/reports/01-13-25percentoffset.pdf ; https://www.jct.gov/getattachment/6a046715-7bc7-4687-9749-2b02a9cba0de/x-10-25.pdf',
  'WP-115 p.11: the income tax effect "is assumed to reduce the amount of gross carbon tax revenues available ... by 25 percent." JCT: a rebate that is taxable and not income-limited carries no offset.'),
 ('R2-05', 'S&P 500 companies: market value and latest annual headcount, firm by firm (29,672,422 employees worldwide)',
  'stockanalysis.com S&P 500 list (Oct 16, 2026 close) and company employee pages (citing filings); six counts replaced from 10-Ks',
  'research/a5_sp500_firms.csv', 'https://stockanalysis.com/list/sp-500-stocks/ ; https://stockanalysis.com/stocks/TICKER/employees/',
  'Headcounts are worldwide. Used only for the value-per-employee buckets behind the per-person cap.'),
 ('R2-06', 'Share of U.S. corporate equity held in taxable accounts: 27% (2022)', 'Rosenthal and Mucciolo, "Who\'s Left to Tax?", Tax Notes Federal, Apr 1, 2024 (Tax Policy Center)',
  'Table 5', 'https://taxpolicycenter.org/sites/default/files/publication/165884/ssrn-id4797771.pdf', 'Foreign holders 42%, retirement accounts about 27%.'),
 ('R2-07', 'Marginal tax rate on labor income: 27% in 2018 (18 income, 9 payroll); payroll 6.2% + 1.45% each side, 2025 wage base $176,100',
  'CBO, "Marginal Federal Tax Rates on Labor Income: 1962 to 2028" (Jan 24, 2019); SSA', 'Chartbook and data', 'https://www.cbo.gov/publication/54911', ''),
 ('R2-08', 'S&P 500 as-reported earnings, 12 months to Sep 2025: $1,994.76 billion', 'S&P Dow Jones Indices, Q3 2025 buyback release (Dec 18, 2025)', 'Annual table',
  'https://press.spglobal.com/2025-12-18-S-P-500-Q3-2025-Buybacks-Post-Modest-6-2-Gain-to-249-0-Billion-After-Declining-20-1-Amidst-Uncertainty-in-Q2-Q4-2025-Expenditures-Expected-to-Post-Similar-Growth,-As-2025-Anticipates-a-Record-1-Trillion', ''),
 ('R2-09', 'S&P 500 1997-2011: year-end market value, dividends, gross buybacks, earnings, price and total return',
  'S&P DJI release tables (2007-2011); S&P-sourced charts digitized from Yardeni Research and ECB Financial Stability Review Dec 2005 (1998-2006); Slickcharts returns',
  'research/a1_sp500_annual_1997_2011.csv (each cell tagged); digitization checked against S&P figures for 2007-2016 (largest error 0.8%)',
  'https://archive.yardeni.com/pub/buybackdiv.pdf ; https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2005/pdf/ecb~84be0ee809.fsrbox200512_01.pdf ; https://www.slickcharts.com/sp500/returns',
  'Digitized values carry chart-reading error of about 1%.'),
 ('R2-10', 'Damodaran implied-premium data: S&P 500 year-end levels (1257.60, 1426.19, 1848.36 for 2011-2013), dividends plus buybacks per index unit',
  'Aswath Damodaran, histimpl.xls (saved Jan 2026)', "Sheet 'Historical Impl Premiums'", 'https://pages.stern.nyu.edu/~adamodar/pc/datasets/histimpl.xls', ''),
 ('R2-11', 'Starter-home median sale price $260,508 (Aug 2025)', 'Redfin, starter home report', 'August 2025', 'https://www.redfin.com/news/starter-home-report-august-2025/', 'Starter = 5th to 35th percentile of prices.'),
 ('R2-12', "First-time buyers: 21% of buyers, median age 40, median down payment 10%", 'NAR, 2025 Profile of Home Buyers and Sellers (Nov 4, 2025)', 'Highlights',
  'https://www.nar.realtor/research-and-statistics/research-reports/highlights-from-the-profile-of-home-buyers-and-sellers', ''),
 ('R2-13', 'Tenure with current employer, January 2026: distribution (Table 3) and medians (Table 1); median 4.1 years', 'BLS, Employee Tenure in 2026 (USDL-26-1532, Sept 24, 2026)', 'Tables 1 and 3',
  'https://www.bls.gov/news.release/tenure.htm', 'The separation hazards by tenure in this workbook are fitted to Table 3 (hazard.py).'),
 ('R2-14', 'Separations at establishments with 5,000+ employees, 2021-2025 (yearly rates computed from monthly data): 22.7% to 18.2%',
  'BLS JOLTS database (file dated Sept 29, 2026)', 'Size class 6', 'https://www.bls.gov/news.release/jolts.t14.htm', 'Computed; BLS publishes no annual rates by size class.'),
 ('R2-15', 'Where workers leaving 500+ employee firms go (2024): 34.0% to another 500+ firm, 18.9% to a smaller private firm, 2.5% public sector, 41.0% persistent nonemployment',
  'Census LEHD Job-to-Job Flows, release R2026Q3', 'Computed from national and state files', 'https://lehd.ces.census.gov/data/j2j/latest_release/', ''),
 ('R2-16', 'Vesting and payout law for employee ownership plans', '26 U.S.C. 411(a)(2)(B); 26 U.S.C. 409(o), 409(h)', 'Statute',
  'https://www.law.cornell.edu/uscode/text/26/411 ; https://www.law.cornell.edu/uscode/text/26/409',
  '411: 100% after 3 years, or 20/40/60/80/100% at 2-6 years. 409(o): payouts start within 1 year after the plan year of retirement (5 years for other separations), in at most 5 yearly installments.'),
 ('R2-17', 'ESOPs: 6,609 plans, 15.1 million participants, $2.06 trillion; companies buy back a median 5% of shares a year', 'NCEO, Employee Ownership by the Numbers (Jan 2026); 2023 repurchase obligation survey', '',
  'https://www.nceo.org/research/employee-ownership-by-the-numbers ; https://www.nceo.org/employee-ownership-blog/2023-repurchase-obligation-survey-results-now-available', ''),
 ('R2-18', "France's mandatory profit sharing: total pay rises with no base-pay cut on average; high-skill workers' base pay falls by about what they receive (about 100% offset); low and intermediate skill about 0%",
  'Nimier-David, Sraer and Thesmar, NBER Working Paper 31804 (revised Aug 2025)', 'Tables 7-10 and Section 6',
  'https://nber.org/system/files/working_papers/w31804/w31804.pdf', 'The 95% interval rules out more than about 14 cents of crowd-out per euro on average.'),
 ('R2-19', 'Mandatory profit sharing shows zero substitution for wages; voluntary schemes near-complete', "Conseil d'analyse economique, Note 79 (July 2023)", '', 'https://cae-eco.fr/static/pdf/cae079-participation-2300720.pdf', ''),
 ('R2-20', 'U.S. evidence: trade-offs between base pay and shared compensation are minimal', 'Kruse, Freeman and Blasi, Shared Capitalism at Work (NBER, 2010), ch. 8', '', 'https://www.nber.org/chapters/c8093.pdf', 'Correlational.'),
 ('R2-21', "Romer's digital ad tax: rising marginal rates on a firm's U.S. digital ad revenue, 0% under $5 billion up to 72.5% above $60 billion; alternative schedule tops out at 50%; his 2021 firm inputs (Microsoft $6.65B U.S.)",
  'Paul Romer, Taxing Digital Advertising (May 17, 2021) and FAQ (May 6, 2019)', 'Rate tables (js files)', 'https://adtax.paulromer.net/ ; https://adtax.paulromer.net/js/load-tables-1.js',
  'His FAQ says the aim is to change behavior ("back side of the Laffer curve"), not to raise revenue.'),
 ('R2-22', 'U.S. internet ad revenue 2025 $294.6 billion; search 38.8%; top 10 companies about 84%', 'IAB/PwC Internet Advertising Revenue Report, FY2025 (Apr 16, 2026)', 'Press release and webinar',
  'https://www.iab.com/news/digital-ad-revenue-climbs-to-nearly-300b-as-iab-celebrates-30-year-anniversary/', ''),
 ('R2-23', 'Company ad revenue 2025: Meta U.S.-and-Canada ads by user location $85.3B, U.S.-billed revenue $74.78B; Alphabet U.S. revenue 48% of total, Google advertising $294.7B worldwide; Amazon advertising $68.6B worldwide, U.S. about $48B (2026 forecast $56.71B less 17.9% growth); TikTok U.S. about $12B; Microsoft search advertising $15.2B worldwide (FY2026); Google, Meta and Amazon about 72% of U.S. digital ad spending',
  'Meta, Alphabet, Amazon, Microsoft 10-Ks (FY2025, FY2026); EMARKETER (2026); WARC via Marketing Dive (2025); EMARKETER via PPC Land (Aug 29, 2025)', 'Revenue notes and geography tables',
  'https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm ; https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm ; https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm ; https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm ; https://emarketer.com/press-releases/meta-to-surpass-google-in-digital-ad-revenues-for-first-time-ever ; https://www.emarketer.com/content/faq-on-amazon-advertising--retail-media-dominance--prime-video-scale--agentic-ad-tools ; https://www.marketingdive.com/news/tiktok-ad-revenue-could-top-30-billion-ban-us/742056/ ; https://ppc.land/digital-advertising-triopoly-gains-overall-market-share-while-facing-competition/',
  "No company reports U.S. ad revenue alone, so each firm is a low-high range."),
 ('R2-24', "State ad taxes, Oct 2026: Maryland's struck by its Tax Court (Aug 14, 2026; on appeal); Washington taxes ad services since Oct 1, 2025; Illinois 10% tax on targeted ads from Jan 1, 2027 (sued); Utah 4.70% from 2027 (sued)",
  'Maryland Tax Court, Apple v. Comptroller (No. 23-DA-OO-0456); 4th Cir. No. 24-1727; WA DOR; Illinois P.A. 104-0468; Utah S.B. 287', '',
  'https://taxcourt.maryland.gov/PDF/Decisions/23-DA-OO-0456-APPLE-FINAL-ORDER.pdf ; https://www.ca4.uscourts.gov/opinions/241727.P.pdf ; https://www.ilga.gov/documents/legislation/PublicActs/104/104-0468.htm ; https://le.utah.gov/Session/2026/bills/enrolled/SB0287.pdf', ''),
 ('R2-25', 'Who bears digital ad taxes: Amazon passed about half of European digital services taxes into seller fees; a tax on Facebook raised its ad prices 25%-38%',
  'Langenmayr and Muddasani (2025); Lassmann et al., European Economic Review 172 (2025)', '',
  'https://storage.e.jimdo.com/file/b2f10b20-f37c-4d9b-8d16-d86f91b1b04f/2025_05%20DST.pdf ; https://e-archivo.uc3m.es/rest/api/core/bitstreams/0017f18d-3a28-4c64-acd4-b7b310610578/content', ''),
 ('R2-26', 'Energy CO2: 2005 6,007.5 MMT; 2025 4,904.4; AEO2026 counterfactual baseline 4,431 (2030), 3,844 (2035), 3,656 (2040), 3,791 (2050)',
  'EIA (July 2026 emissions report; Annual Energy Outlook 2026, Apr 8, 2026)', 'Table 18', 'https://www.eia.gov/environment/emissions/carbon/ ; https://www.eia.gov/outlooks/aeo/excel/aeotab18.xlsx', ''),
 ('R2-27', 'U.S. 2035 NDC: 61%-66% below 2005 (submitted Dec 2024; the U.S. left Paris Jan 27, 2026)', 'UNFCCC', '', 'https://unfccc.int/sites/default/files/2024-12/United%20States%202035%20NDC.pdf',
  'Computed decline from 2025: 7.1%-8.4% a year. Used for the fast-decarbonization test at 7.5%.'),
 ('R2-28', 'RFF projections with the Baker-Shultz fee: 4.1 (2021), 3.7 (2025), 3.3 (2030), 3.0 (2035) billion tons; without: 5.1, 5.0, 4.9, 4.8', 'Resources for the Future, Issue Brief 18-07 (rev. Mar 2019), Table 1a', '',
  'https://www.rff.org/documents/2046/RFF-IB-18-07-rev_4evu2ny.pdf', 'No source projects the fee path past 2035; later carbon checks are extrapolations.'),
 ('R2-29', 'Closely held corporate equity $15.637 trillion (S corporations $12.070 trillion), 2026:Q2', 'Federal Reserve, Financial Accounts Z.1 (Sept 11, 2026)', 'F.51.1.s',
  'https://www.federalreserve.gov/releases/z1/current/html/F51_1_s.htm', 'All sizes; no public source gives the value above the size line.'),
 ('R2-30', 'Firms with 500+ employees: 21,041 firms, 73.5 million jobs (54.1%), 2022', 'Census, Statistics of U.S. Businesses 2022 (Apr 10, 2025)', '', 'https://www.census.gov/programs-surveys/susb.html', 'Includes public, private, foreign-owned and nonprofit employers.'),
 ('R2-31', 'U.S. affiliates of foreign companies, 2024: 8.57 million jobs (6.1% of private jobs), sales $6.518 trillion, value added $1.518 trillion', 'BEA (July 10, 2026)', '',
  'https://www.bea.gov/news/2026/activities-us-affiliates-foreign-multinational-enterprises-2024', ''),
 ('R2-32', "America's Top Private Companies 2025: 200 firms, $2.02 trillion revenue, 3.88 million employees", 'Forbes (Dec 17, 2025)', 'List data', 'https://www.forbes.com/lists/top-private-companies/', 'Totals summed from the list.'),
 ('R2-33', 'About half of large S&P 500 firms\' gross repurchases in 1994-98 were offset by employee option exercises', 'Liang and Sharpe, Federal Reserve FEDS 1999-59', 'Abstract',
  'https://www.federalreserve.gov/pubs/feds/1999/199959/199959abs.html', 'Basis for the half-offset variant of the replays.'),
 ('R2-34', 'AI spending and payouts, 2025-2026: Alphabet, Meta zero buybacks in H1 2026; nonfinancial companies net issuers of stock in Q1-Q2 2026; Q1 2026 buybacks +1% vs capex +38%',
  'Company filings; Fed Z.1 via FRED NCBCEBQ027S; Goldman Sachs via Yahoo Finance and Fortune (2026)', '',
  'https://fred.stlouisfed.org/series/NCBCEBA027N ; https://fortune.com/2026/06/17/why-cant-i-get-a-raise-data-centers-buybacks-offshoring-goldman-oppenheimer/', 'The 1.5% cash yield in the AI tests is illustrative.'),
 ('R2-35', "Tax status: Alaska's dividend is federally taxable; state entities excluded under 26 U.S.C. 115; the federal Railroad Retirement Investment Trust is exempt by name in 501(c)(28)",
  'Alaska PFD Division; 26 U.S.C. 115, 501(c)(28)', '', 'https://pfd.alaska.gov/Payments/Tax-Information ; https://www.law.cornell.edu/uscode/text/26/115', 'A federal citizen trust would need an explicit exemption.'),
 ('R2-36', 'Shiller CAPE: Dec 1999 44.20, Dec 2000 37.27, Dec 2007 25.96, Dec 2008 15.38, Sep 2026 40.58', 'multpl.com (Shiller data)', 'By month', 'https://www.multpl.com/shiller-pe/table/by-month', ''),
 ('R2-37', "Canada ended its consumer carbon price Apr 1, 2025; Finance Canada said 8 in 10 families got back more than they paid (Feb 14, 2024)", 'Finance Canada', '',
  'https://www.canada.ca/en/department-finance/news/2025/03/removing-the-consumer-carbon-price-effective-april-1-2025.html ; https://www.canada.ca/en/department-finance/news/2024/02/government-announces-canada-carbon-rebate-amounts-for-2024-25.html', ''),
 ('R2-38', "Mexico's 2021 reform capped profit sharing at three months' pay or the three-year average, whichever is higher", 'Basham, Ringe y Correa (Apr 4, 2024); IZA DP 18566 (Apr 2026)', '',
  'https://basham.com.mx/profit-sharing-maximum-payment-limit-validation/ ; https://docs.iza.org/dp18566.pdf', ''),
 ('R2-39', 'FHA minimum down payment 3.5% (credit score 580+); 30-year mortgage averaged 6.60% in 2025', 'HUD; Freddie Mac PMMS (weekly, averaged)', '', 'https://www.hud.gov/helping-americans/loans ; https://www.freddiemac.com/pmms', ''),
 ('R2-40', 'Federal brackets 2025 (married filing jointly) and 2025 standard deduction $31,500', 'IRS IR-2024-273; IR-2025-103', '', 'https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill', ''),
 ('R2-41', 'The round-two engine: the plan as plain code, tenure-based worker model, stress paths', 'engine.py, scenarios.py, score.py, family.py, hazard.py, analysis.py (in the SOMA folder, engine subfolder)', '', '',
  'Anyone can rerun every number on the Best combination tab.'),
]
