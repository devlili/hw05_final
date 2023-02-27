from django.test import TestCase

from ..models import Comment, Group, Post


class ModelTest(TestCase):
    """Тестирование моделей."""

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""

        group = Group(title="Тестовая группа")
        long_post = Post(text="Это очень объемный пост")
        short_post = Post(text="Короткий пост")
        comment = Comment(text="Тестовый комментарий")
        expected_object_name = [
            (str(group), "Тестовая группа"),
            (str(long_post), "Это очень объем"),
            (str(short_post), "Короткий пост"),
            (str(comment), "Тестовый коммен"),
        ]
        for value, expected in expected_object_name:
            with self.subTest(value=value):
                self.assertEqual(
                    value,
                    expected,
                    f"У модели {value} некорректно работает __str__",
                )
