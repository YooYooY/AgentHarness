-- ============================================================================
-- Project: food / IELTS Chapter 2 — Food Core Shadowing Passages
-- File: db/seed.sql
-- Description: Initial seed data, based on the content in food.md.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- Themes
-- ----------------------------------------------------------------------------
INSERT INTO themes (slug, name, sort_order) VALUES
    ('daily-meals-fruit-vegetables', 'Daily Meals, Fruit and Vegetables', 1);

-- ----------------------------------------------------------------------------
-- Passages — Theme 1, Passage 1 (A: everyday English)
-- ----------------------------------------------------------------------------
INSERT INTO passages (theme_id, passage_type, title, content, core_chunks, retelling_map, output_ladder)
VALUES (
    1,
    'A',
    'What I Normally Eat in a Day',
    'My eating habits are quite simple on weekdays. I normally start the day with two eggs, a cup of yogurt, and some fruit. I used to skip breakfast when I was in a hurry, but I found that I could not concentrate well before lunch. At midday, I usually have rice or noodles with chicken and at least one vegetable, such as spinach, cabbage, or carrots. Dinner depends on how much time I have. If I finish work early, I prepare a proper meal with soup and fresh vegetables. Otherwise, I may order something convenient. I also keep bananas or apples at home because they make a quick and nutritious snack. My diet is not perfect, and I still eat fast food occasionally. However, I try to maintain a reasonable balance instead of following a strict diet that would be difficult to continue.',
    '["eating habits", "start the day with", "skip breakfast", "concentrate well", "a proper meal", "a quick and nutritious snack", "maintain a reasonable balance", "follow a strict diet"]',
    '["breakfast", "reason for not skipping it", "lunch", "dinner", "snacks", "overall opinion"]',
    '["One sentence: I normally have ___ for breakfast because ___.", "Three sentences: Describe your breakfast, lunch, and dinner.", "One minute: Describe everything you normally eat on a weekday."]'
);

-- ----------------------------------------------------------------------------
-- Shadowing sections for the passage above
-- ----------------------------------------------------------------------------
INSERT INTO passage_sections (passage_id, section_order, text) VALUES
    (1, 1, 'My eating habits are quite simple on weekdays. / I normally start the day with two eggs, a cup of yogurt, and some fruit.'),
    (1, 2, 'I used to skip breakfast when I was in a hurry, / but I found that I could not concentrate well before lunch.'),
    (1, 3, 'At midday, I usually have rice or noodles with chicken / and at least one vegetable, such as spinach, cabbage, or carrots.'),
    (1, 4, 'Dinner depends on how much time I have. / If I finish work early, I prepare a proper meal with soup and fresh vegetables.'),
    (1, 5, 'Otherwise, I may order something convenient. / I also keep bananas or apples at home because they make a quick and nutritious snack.'),
    (1, 6, 'My diet is not perfect, / and I still eat fast food occasionally. / However, I try to maintain a reasonable balance / instead of following a strict diet that would be difficult to continue.');
