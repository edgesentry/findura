-- Query Version: insurer-open-findings-v1
-- Description: Deterministic insurer profile query for renewal view
-- Requires %(as_of)s::date parameter; no current clock functions permitted

-- 1. Open Findings (unremediated defects)
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
WHERE r.completed = FALSE
ORDER BY
    b.building_key ASC,
    (d.due_on < %(as_of)s::date) DESC,
    d.due_on ASC,
    f.finding_key ASC;
