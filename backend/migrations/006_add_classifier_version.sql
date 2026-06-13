ALTER TABLE ai_classifications ADD COLUMN IF NOT EXISTS classifier_version VARCHAR(64);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_classifier_version ON ai_classifications(classifier_version);

-- Backfill classifier_version for existing rule-based classifications
UPDATE ai_classifications
SET classifier_version = 'rule_v1'
WHERE classifier_version IS NULL
  AND model = 'stub';
