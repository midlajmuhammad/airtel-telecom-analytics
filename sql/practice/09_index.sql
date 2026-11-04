-- Tool 9: CREATE INDEX and EXPLAIN QUERY PLAN (compare plan before and after an index)
EXPLAIN QUERY PLAN
SELECT book FROM loans WHERE member_id = 1;

CREATE INDEX IF NOT EXISTS ix_loans_member
    ON loans(member_id);

EXPLAIN QUERY PLAN
SELECT book FROM loans WHERE member_id = 1;

SELECT book
FROM loans
WHERE member_id = 1;