-- ==================================================
-- 01_revenue_customer.sql
-- What this file fixes : What each subscriber paid
-- Defect numbers       : 1 and 6 from tab 3
-- Window               : 2025-01-01 to 2025-06-30
-- Written by           : Your Name
-- ==================================================

DROP VIEW IF EXISTS v_revenue_customer;

CREATE VIEW v_revenue_customer AS

SELECT
    c.customer_id,

    COALESCE(r.n_payments, 0) AS recharge_count,

    COALESCE(r.total_inr, 0) AS recharge_total_6m,

    ROUND(
        COALESCE(r.total_inr, 0) / 6.0,
        2
    ) AS actual_arpu_6m

FROM customers c

LEFT JOIN (
    SELECT
        customer_id,
        COUNT(*) AS n_payments,
        SUM(amount_inr) AS total_inr

    FROM recharges

    WHERE recharge_date BETWEEN '2025-01-01'
                            AND '2025-06-30'

    GROUP BY customer_id

) r
ON r.customer_id = c.customer_id;