-- Tool 8: Running totals (count loans and books still out so far)
SELECT loan_date,
       book,
       COUNT(*) OVER (ORDER BY loan_date, loan_id) AS loans_so_far,
       SUM(returned_on IS NULL) OVER (ORDER BY loan_date, loan_id) AS out_so_far
FROM loans
ORDER BY loan_date, loan_id;