-- Tool 6: EXISTS and NOT EXISTS (check for at least one loan or no loans)
SELECT m.name
FROM members AS m
WHERE EXISTS (
    SELECT 1
    FROM loans AS l
    WHERE l.member_id = m.member_id
      AND l.returned_on IS NULL
)
ORDER BY m.member_id;

SELECT m.name
FROM members AS m
WHERE NOT EXISTS (
    SELECT 1
    FROM loans AS l
    WHERE l.member_id = m.member_id
)
ORDER BY m.member_id;