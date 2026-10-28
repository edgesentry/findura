-- Query Version: insurer-completed-remediations-v1
-- Description: Deterministic insurer profile point-in-time renewal query for completed remediations.
-- Semantics:
--   Selects remediations completed on or before %(as_of)s::date.
-- Parameter: %(as_of)s::date (strictly bound, wall-clock functions forbidden).

SELECT
    b.building_key AS building,
    a.asset_key AS asset,
    TO_CHAR(i.conducted_on, 'YYYY-MM-DD') AS conducted_on,
    f.finding_key AS finding_id,
    f.statement AS finding_statement,
    TO_CHAR(d.due_on, 'YYYY-MM-DD') AS due_on,
    TO_CHAR(r.completed_on, 'YYYY-MM-DD') AS completed_on,
    FALSE AS overdue
FROM findings f
JOIN inspections i ON f.inspection_id = i.id
JOIN assets a ON i.asset_id = a.id
JOIN buildings b ON a.building_id = b.id
JOIN deadlines d ON d.finding_id = f.id
JOIN remediations r ON r.finding_id = f.id
WHERE r.completed = TRUE
  AND r.completed_on IS NOT NULL
  AND r.completed_on <= %(as_of)s::date
ORDER BY
    b.building_key ASC,
    r.completed_on DESC,
    d.due_on ASC,
    f.finding_key ASC;
