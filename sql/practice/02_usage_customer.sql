

DROP VIEW IF EXISTS v_usage_customer;

CREATE VIEW v_usage_customer AS

SELECT
    c.customer_id,

    COALESCE(u.usage_days, 0) AS usage_days,

    COALESCE(u.total_mb, 0) AS total_data_mb,

    COALESCE(u.total_voice, 0) AS total_voice_min,

    COALESCE(u.total_sms, 0) AS total_sms,

    COALESCE(u.roaming_days, 0) AS roaming_days,

    ROUND(
        u.total_mb / u.usage_days,
        2
    ) AS mb_per_active_day,

    ROUND(
        COALESCE(u.total_mb, 0) / 181.0,
        2
    ) AS mb_per_observed_day,

    u.last_usage_date,

    CAST(
        julianday('2025-06-30')
        - julianday(u.last_usage_date)
        AS INT
    ) AS recency_days

FROM customers c

LEFT JOIN (
    SELECT
        customer_id,

        COUNT(*) AS usage_days,

        SUM(data_mb) AS total_mb,

        SUM(voice_minutes) AS total_voice,

        SUM(sms_count) AS total_sms,

        SUM(is_roaming) AS roaming_days,

        MAX(usage_date) AS last_usage_date

    FROM usage_daily

    GROUP BY customer_id

) u
ON u.customer_id = c.customer_id;


