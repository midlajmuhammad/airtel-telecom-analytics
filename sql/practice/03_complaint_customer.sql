
DROP VIEW IF EXISTS v_complaint_customer;

CREATE VIEW v_complaint_customer AS

SELECT
    c.customer_id,

    COALESCE(x.n_total, 0) AS complaint_count,

    COALESCE(x.n_open, 0) AS unresolved_count,

    COALESCE(x.n_closed, 0) AS resolved_count,

    x.avg_resolution_days

FROM customers c

LEFT JOIN (
    SELECT
        customer_id,

        COUNT(*) AS n_total,

        SUM(
            CASE
                WHEN is_resolved = 0
                THEN 1
                ELSE 0
            END
        ) AS n_open,

        SUM(
            CASE
                WHEN is_resolved = 1
                THEN 1
                ELSE 0
            END
        ) AS n_closed,

        ROUND(
            AVG(resolution_days),
            2
        ) AS avg_resolution_days

    FROM complaints

    GROUP BY customer_id

) x
ON x.customer_id = c.customer_id;
