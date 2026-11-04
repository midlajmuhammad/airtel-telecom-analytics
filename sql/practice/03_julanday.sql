-- Tool 3: julianday() (calculate how long returned books were out)
SELECT book,
       CAST(julianday(returned_on) - julianday(loan_date) AS INT) AS days_out
FROM loans
WHERE returned_on IS NOT NULL
ORDER BY loan_id;

SELECT ROUND(AVG(julianday(returned_on) - julianday(loan_date)), 1) AS avg_days,
       MIN(julianday(returned_on) - julianday(loan_date)) AS min_days,
       MAX(julianday(returned_on) - julianday(loan_date)) AS max_days
FROM loans
WHERE returned_on IS NOT NULL;