# Sunrise Coffee Performance Review

**Two years of trading across 60 UK coffee shops. One estate margin, and a set of problems the average hides.**

This repo holds the analysis I rebuilt from the supplied DataDNA challenge extract. It covers store and regional profitability, loyalty programme effectiveness, revenue mix, seasonal patterns and store-level profit movement.

![Python](https://img.shields.io/badge/Python-pandas%20%7C%20matplotlib-3776AB)
![Data](https://img.shields.io/badge/Data-5%20CSV%20tables-217346)
![Status](https://img.shields.io/badge/status-complete-success)

---

## Headline result

The estate made **£16.88M net profit on £89.69M revenue** over 2023 and 2024, an **18.8 percent net margin**. The average is not the story.

| Finding | Verified figure |
|---|---|
| Weakest region | London, 8.45 percent margin, 25.6 percent of store-months loss-making |
| Strongest region | Northern-Ireland, 28.43 percent margin |
| December 2024 loss-makers | 8 of 60 stores, including 1 Structural-Loss store |
| Loyalty revenue share | 33.2 percent of two-year revenue (£29.77M) |
| Loyalty redemption cost | 1.93 percent of revenue (£1.73M) |
| Loyalty and basket size | Correlation minus 0.063, so no useful link |
| Revenue mix 2023 to 2024 | Food 26.24 percent to 25.90 percent, beans 8.90 percent to 9.20 percent |
| Bank holiday trading | £1,347 average per recorded store-day against £2,054 on standard days |

The original workbook's cached KPI cards are not used as source figures. Several of them contradict the raw data, for example 59 profitable plus 41 loss-making stores from a 60-store estate. The analysis is recomputed from the five CSV tables.

## Repository structure

```
sunrise-coffee-performance/
├── data/                         # five supplied CSV tables, read-only
│   ├── dim_store.csv             # 60 stores
│   ├── dim_product.csv           # 40 products
│   ├── dim_date.csv              # 730 days, 2023-01-01 to 2024-12-30
│   ├── fact_daily_sales.csv      # 10,000 recorded store-days
│   └── fact_store_monthly_profitability.csv  # 1,440 store-months
├── docs/
│   ├── CHALLENGE_BRIEF.md        # the supplied brief
│   ├── DATA_DICTIONARY.md        # the supplied dictionary, with known errors
│   └── ANALYSIS_NOTES.md         # verified figures and source issues
├── scripts/
│   ├── analyse.py                # all joins, cuts, metrics and quality checks
│   ├── make_charts.py            # six titled report figures
│   └── qa_check.py               # rebuilds the headline numbers as assertions
├── outputs/
│   ├── summary.json              # single source for every published number
│   └── charts/                   # six report PNG figures
├── workbook/
│   ├── Sunrise Coffee_.xlsx      # supplied workbook, left untouched
│   └── E226AA60                  # extensionless source archive, left untouched
├── screenshots/                  # supplied images and dashboard captures
└── README.md
```

## Run it

```bash
pip install pandas numpy matplotlib
python scripts/analyse.py
python scripts/make_charts.py
python scripts/qa_check.py
```

There is no random step, no network call and no manual spreadsheet edit. Re-running produces the same summary and charts. The CSVs and the workbook are read-only inputs.

## What the data says

- London is the margin drag. It carries £10.46M of revenue but only £0.88M of profit over two years.
- The brief names three store formats, but the data has only High-Street (58 stores) and Transport-Hub (2 stores). I do not use format as an expansion rule.
- Loyalty adoption and member revenue share correlate at 0.998, which is close to mechanical in this data. Adoption and recomputed transaction value correlate at minus 0.063.
- Food revenue share did not grow. It fell by 0.34 percentage points from 2023 to 2024.
- November was the worst month of 2023 and the best month of 2024. Month-of-year seasonality is not stable here.
- The daily table covers 10,000 of 43,800 possible store-days, so weekday and holiday cuts describe recorded rows, not a full estate census.

## Known source issues

- `dim_date` ends on 30 December 2024 although the brief says 31 December 2024.
- The data dictionary claims product gross margin is 36 to 80 percent. The actual range is 66.0 to 90.4 percent.
- The workbook's `week_num` column holds day of week, not week number.
- 27 of 28 workbook charts have no title, and the Product, Loyalty and Store tabs contain no cell values.
- Store status counts in the workbook overlap, so Profitable plus Loss-Making exceeds the 60-store estate.

Full detail is in `docs/ANALYSIS_NOTES.md` and in the technical page of the portfolio case study.

## Author

Built by [Elice Bassey](https://github.com/Elice99). The case study, business insights and technical documentation are on [the portfolio](https://elishabassey.netlify.app).
