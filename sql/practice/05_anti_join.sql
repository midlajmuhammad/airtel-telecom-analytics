-- Tool 5: Anti-join (find members who have never borrowed a book)
SELECT m.name
FROM members AS m
LEFT JOIN loans AS l
    ON l.member_id = m.member_id
WHERE l.member_id IS NULL;