-- Tool 2: Roll up first, then LEFT JOIN to keep every member
WITH l AS (
    SELECT member_id,
           COUNT(*) AS books
    FROM loans
    GROUP BY member_id
)
SELECT m.name,
       COALESCE(l.books, 0) AS books
FROM members AS m
LEFT JOIN l
    ON l.member_id = m.member_id
ORDER BY m.member_id;
