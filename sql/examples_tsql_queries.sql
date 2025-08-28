-- Q1: Top 10 institutions by 4-year retention (size threshold)
SELECT TOP 10 INSTNM, STABBR, CONTROL, UGDS, RETENTION_FT_4YR
FROM dbo.Scorecard
WHERE UGDS >= 2000 AND RETENTION_FT_4YR IS NOT NULL
ORDER BY RETENTION_FT_4YR DESC;

-- Q2: Completion by Pell-share bucket (equity lens)
WITH Buckets AS (
  SELECT *,
    CASE
      WHEN PELL_SHARE < 20 THEN 'Low Pell'
      WHEN PELL_SHARE BETWEEN 20 AND 40 THEN 'Mid Pell'
      ELSE 'High Pell'
    END AS PellBucket
  FROM dbo.Scorecard
)
SELECT PellBucket,
       AVG(COMPLETION_150_4YR) AS AvgCompletion4yr,
       COUNT(*) AS Institutions
FROM Buckets
GROUP BY PellBucket
ORDER BY CASE WHEN PellBucket='Low Pell' THEN 1 WHEN PellBucket='Mid Pell' THEN 2 ELSE 3 END;

-- Q3: State-level overview for a one-pager brief
SELECT STABBR,
       AVG(RETENTION_FT_4YR)   AS Retention4yr_Avg,
       AVG(COMPLETION_150_4YR) AS Completion4yr_Avg,
       AVG(TUITIONFEE_IN)      AS Tuition_InState_Avg
FROM dbo.Scorecard
GROUP BY STABBR
ORDER BY STABBR;
