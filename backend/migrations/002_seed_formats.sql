INSERT INTO formats (label, description, is_faceless_friendly, is_ai_friendly, repeatability_prior)
VALUES
  ('tutorial / guide', 'Step-by-step educational format with a clear how-to promise.', true, true, 0.85),
  ('mistakes / lessons', 'List of errors, lessons learned, or anti-patterns.', true, true, 0.80),
  ('review / comparison', 'Product, tool, creator, or concept comparison.', true, false, 0.75),
  ('experiment / challenge', 'Creator performs a test, challenge, or personal experiment.', false, false, 0.65),
  ('case study / explainer', 'Narrative breakdown explaining why something worked or happened.', true, true, 0.90),
  ('unknown / needs AI', 'Fallback label before stronger AI classification.', null, null, 0.35)
ON CONFLICT (label) DO UPDATE SET
  description = EXCLUDED.description,
  is_faceless_friendly = EXCLUDED.is_faceless_friendly,
  is_ai_friendly = EXCLUDED.is_ai_friendly,
  repeatability_prior = EXCLUDED.repeatability_prior;

INSERT INTO niches (label, parent_label, description)
VALUES
  ('AI tools', 'technology', 'Tools and workflows around artificial intelligence.'),
  ('business / money', 'business', 'Entrepreneurship, income, investing, startups, and monetization.'),
  ('health / fitness', 'lifestyle', 'Fitness, health optimization, nutrition, and workout content.'),
  ('gaming', 'entertainment', 'Gaming videos, challenges, commentary, and game-specific channels.'),
  ('history', 'education', 'History explainers, stories, conflicts, and historical analysis.'),
  ('unknown', null, 'Fallback label before stronger AI classification.')
ON CONFLICT (label) DO UPDATE SET
  parent_label = EXCLUDED.parent_label,
  description = EXCLUDED.description;
