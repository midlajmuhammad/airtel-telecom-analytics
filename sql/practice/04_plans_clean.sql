DROP VIEW IF EXISTS v_plans_clean;

CREATE VIEW v_plans_clean AS

SELECT
    plan_id,
    plan_name,
    plan_type,
    price_inr,
    validity_days,
    data_quota,

    CASE
        WHEN INSTR(data_quota, '/day') > 0
        THEN 'per day'

        WHEN INSTR(data_quota, '/month') > 0
        THEN 'per month'
    END AS quota_basis,

    CAST(
        SUBSTR(
            data_quota,
            1,
            INSTR(data_quota, ' ') - 1
        )
        AS REAL
    ) AS quota_gb,

    CASE
        WHEN INSTR(data_quota, '/day') > 0
        THEN
            CAST(
                SUBSTR(
                    data_quota,
                    1,
                    INSTR(data_quota, ' ') - 1
                )
                AS REAL
            ) * 30

        ELSE
            CAST(
                SUBSTR(
                    data_quota,
                    1,
                    INSTR(data_quota, ' ') - 1
                )
                AS REAL
            )
    END AS monthly_gb,

    ott_benefit,
    is_5g

FROM plans;