-- Query Version: insurer-open-findings-v1
-- Description: Deterministic insurer profile point-in-time renewal query for open findings.
-- Semantics:
--   Selects findings discovered on or before %(as_of)s::date that were NOT yet remediated
--   as of the reference date (either uncompleted, or completed strictly after as_of).
-- Parameter: %(as_of)s::date (strictly bound, wall-clock functions forbidden).

SELECT
    b.building_key AS building,
    a.asset_key AS asset,
    TO_CHAR(i.conducted_on, 'YYYY-MM-DD') AS conducted_on,
    f.finding_key AS finding_id,
    f.statement AS finding_statement,
    TO_CHAR(d.due_on, 'YYYY-MM-DD') AS due_on,
    NULL AS completed_on,
    (d.due_on < %(as_of)s::date) AS overdue
FROM findings f
JOIN inspections i ON f.inspection_id = i.id
JOIN assets a ON i.asset_id = a.id
JOIN buildings b ON a.building_id = b.id
JOIN deadlines d ON d.finding_id = f.id
JOIN remediations r ON r.finding_id = f.id
WHERE f.found_on <= %(as_of)s::date
  AND (
      r.completed = FALSE
      OR r.completed_on IS NULL
      OR r.completed_on > %(as_of)s::date
  )
ORDER BY
    b.building_key ASC,
    (d.due_on < %(as_of)s::date) DESC,
    d.due_on ASC,
    f.finding_key ASC;
