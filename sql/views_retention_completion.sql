-- View that powers dashboard rollups
IF OBJECT_ID('dbo.vw_RetentionCompletion','V') IS NOT NULL DROP VIEW dbo.vw_RetentionCompletion;
GO
CREATE VIEW dbo.vw_RetentionCompletion AS
SELECT
  STABBR,
  CONTROL,
  PREDDEG,
  COUNT(*)                                  AS Institutions,
  AVG(RETENTION_FT_4YR)   AS RetentionFT4_Avg,
  AVG(COMPLETION_150_4YR) AS Completion4_Avg,
  AVG(RETENTION_FT_2YR)   AS RetentionFT2_Avg,
  AVG(COMPLETION_150_2YR) AS Completion2_Avg
FROM dbo.Scorecard
GROUP BY STABBR, CONTROL, PREDDEG;
GO
