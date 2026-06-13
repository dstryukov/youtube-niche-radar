INSERT INTO formats (label, description, is_faceless_friendly, is_ai_friendly, repeatability_prior)
VALUES
  ('reddit_story', 'Чтение и обсуждение историй с Reddit.', true, true, 0.85),
  ('ai_story', 'Истории, сгенерированные или озвученные AI.', true, true, 0.90),
  ('true_crime', 'Разбор реальных преступлений.', false, false, 0.70),
  ('top_10', 'Списки "Топ 10 ...".', true, true, 0.80),
  ('quiz', 'Викторины, тесты, опросы.', true, true, 0.85),
  ('before_after', 'Трансформации, сравнение до/после.', true, false, 0.75),
  ('history', 'Исторические факты, разборы.', true, true, 0.80),
  ('finance', 'Финансы, инвестиции, личный бюджет.', true, true, 0.75),
  ('reaction', 'Реакция на видео/события.', false, false, 0.60),
  ('facts', 'Факты, подборки, образовательный контент.', true, true, 0.85)
ON CONFLICT (label) DO UPDATE SET
  description = EXCLUDED.description,
  is_faceless_friendly = EXCLUDED.is_faceless_friendly,
  is_ai_friendly = EXCLUDED.is_ai_friendly,
  repeatability_prior = EXCLUDED.repeatability_prior;
