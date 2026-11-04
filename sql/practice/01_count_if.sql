-- Tool 1: SUM and AVG of a condition (count rows where a condition is true)
SELECT member_id,
       COUNT(*) AS loans,
       SUM(returned_on IS NULL) AS still_out
FROM loans
GROUP BY member_id
ORDER BY member_id;

SELECT COUNT(*) AS loans,
       SUM(returned_on IS NULL) AS still_out,
       ROUND(100.0 * AVG(returned_on IS NULL), 1) AS pct_out
FROM loans;
