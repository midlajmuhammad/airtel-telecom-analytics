-- Tool 7: NTILE(n) (split members who borrowed into groups by number of books)
WITH b AS (
    SELECT member_id,
           COUNT(*) AS books
    FROM loans
    GROUP BY member_id
)
SELECT m.name,
       b.books,
       RANK() OVER (ORDER BY b.books DESC) AS rk,
       NTILE(2) OVER (ORDER BY b.books DESC) AS half
FROM b
JOIN members AS m
    ON m.member_id = b.member_id
ORDER BY b.books DESC, m.member_id;