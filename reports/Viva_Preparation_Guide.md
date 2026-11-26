# Airtel Network Usage Dashboard: Viva Preparation

The assignment PDF lists the dashboard topics and technical rules but does not include a separate question bank. The questions below are practice prompts based on those topics. Keep answers tied to the validated SQL and avoid causal claims about the A/B labels.

## Purpose and design

**1. Who is the dashboard for, and what decision does it support?**  
It is for a Network Capacity Planner. It summarizes data demand and subscriber usage patterns to support capacity-planning review.

**2. Why are there two tabs?**  
Overview presents the main patterns. Detail lets the reader select a month and inspect its load, subscriber-level usage, experiment groups, and device categories.

**3. Why use different chart forms?**  
The monthly heatmap compares groups and day denominators in one view. The treemap shows monthly active subscriber counts. Box and violin plots show subscriber-level distributions rather than only averages. Each chart has a title, units or denominator, and the active filter scope.

**4. Which filters are available, and what do they affect?**  
Each chart has an independent Filters popover for circle, date range, customer segment, plan type, region, connection type, and device type. Detail charts also have their own month selector. Sidebar filters affect summary metrics only. The validated T3 test and fixed usage-day total are labelled fixed and do not respond to filters.

**5. How did you keep the tabs compact?**  
Each tab uses a single summary-card row and compact visuals. Each chart's filters open in a popover beside the chart, keeping the controls available without taking up permanent space. Both tabs should be checked full-screen at normal zoom on the smallest class laptop.

## Metric definitions

**6. What is a usage-day?**  
One subscriber with a usage record on one date. A subscriber can have fewer usage-days than calendar days in a month.

**7. What does active subscriber mean?**  
A subscriber with at least one usage-day during the selected month or period.

**8. How are data per usage-day and per calendar day different?**  
For usage-day, each subscriber's data is divided by that subscriber's own usage-days. For calendar-day, data is divided by the number of calendar days in the period. The dashboard averages the subscriber-level values; the denominators are not interchangeable.

**9. How is total data converted to TB?**  
The dashboard divides total MB by 1,024 twice. It uses 1 TB = 1,024 × 1,024 MB and labels the result as TB.

**10. How is allowance utilization calculated?**  
For each subscriber, usage is averaged across the observed months and divided by the plan's monthly data allowance. For plans whose quota is stated per day, the quota is multiplied by 30. The chart shows the subscriber distribution and plan counts; rates are suppressed when a filtered group has fewer than 100 subscribers.

## SQL, data, and interpretation

**11. Where are dashboard metrics calculated?**  
In SQL queries in `dashboard/app.py`, run through the read-only `q()` helper. Python formats the query results for cards and charts; it does not calculate dashboard metrics after the query.

**12. What is the T3 test?**  
It is a validated one-tailed Welch two-sample t-test. The alternative is that group B's mean is greater than group A's. The fixed result is t = 19.45, df = 17,444, p = 1.1e-83, with May–June means of 1,867 MB for B and 1,393 MB for A.

**13. What does the p-value tell you, and what does it not tell you?**  
It measures how unusual the observed test statistic would be under the null model and stated test assumptions. It is not an effect size, does not measure practical importance, and does not prove that the offer caused the difference.

**14. Can the dashboard claim group B caused higher usage?**  
No. A/B are labels in the source data, and the dashboard preserves the validated statistical comparison. Association alone does not establish causation.

**15. Why suppress some group rates?**  
Rates based on fewer than 100 subscribers can be unstable and misleading when shown alone. The dashboard displays counts and omits those rates.

**16. What is the main data model behind the dashboard?**  
`customers` links to `plans` through `current_plan_id`, and to `usage_daily` through `customer_id`. One plan can be assigned to many customers; one customer can have many daily usage records. The full project also contains circles, recharges, and complaints.

## Setup and limitations

**17. How can another person run the project?**  
Install the packages in `requirements.txt`, provide the six source CSVs in `data/raw/`, run `python scripts/build_db.py`, then run `streamlit run dashboard/app.py`. The source data and databases are local and are not committed to Git.

**18. What should be checked before submission?**  
Test All and individual filters, change the Detail month, review chart titles and units, and confirm both tabs fit without scrolling on the smallest laptop at normal zoom. A fresh clone also needs the source dataset before the database can be rebuilt.

## Source

Based on the supplied *Airtel Telecom Analytics — Group 3 — Detailed Dashboard Assignment Guide*, especially its metric definitions, domain cautions, chart restrictions, development workflow, and submission checklist. These are practice answers, not a verbatim question list from the guide.
