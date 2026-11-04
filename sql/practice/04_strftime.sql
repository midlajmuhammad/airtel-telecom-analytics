-- Tool 4: strftime() (group dates into year-month buckets)
SELECT strftime('%Y-%m', loan_date) AS month,
       COUNT(*) AS loans
FROM loans
GROUP BY month
ORDER BY month;