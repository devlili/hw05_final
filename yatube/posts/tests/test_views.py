import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from yatube.settings import POSTS_PER_PAGE

from ..models import Comment, Follow, Group, Post, User

GAP = 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTest(TestCase):
    """Тестирование Views."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Pushkin")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            text="Тестовый комментарий",
            post=cls.post,
            author=cls.user,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_show_correct_context(self):
        """Шаблоны index, group_list, profile сформированы
        с правильным контекстом.
        """

        reverses = (
            reverse("posts:index"),
            reverse("posts:group_list", args=(self.group.slug,)),
            reverse(
                "posts:profile",
                args=(self.user.username,),
            ),
        )
        for reverse_name in reverses:
            response = self.authorized_client.get(reverse_name)
            context = response.context["page_obj"][0]
            contexts = {
                context.text: self.post.text,
                context.author: self.post.author,
                context.group: self.post.group,
                context.image: self.post.image,
            }
            for value, expected in contexts.items():
                with self.subTest(value=value):
                    self.assertEqual(
                        value,
                        expected,
                        "Шаблоны index, group_list, profile сформированы с"
                        " неправильным контекстом",
                    )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse(
                "posts:post_detail",
                args=(self.post.pk,),
            )
        )
        context = response.context["post"]
        contexts = {
            context.text: self.post.text,
            context.author: self.post.author,
            context.group: self.post.group,
            context.image: self.post.image,
        }
        for value, expected in contexts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    value,
                    expected,
                    "Шаблон post_detail сформирован с неправильным контекстом",
                )

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""

        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = [
            ("text", forms.fields.CharField),
            ("group", forms.fields.ChoiceField),
            ("image", forms.fields.ImageField),
        ]
        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(
                    form_field,
                    expected,
                    "Шаблон create_post сформирован с неправильным контекстом",
                )

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно."""

        reverses = (
            reverse("posts:index"),
            reverse("posts:group_list", args=(self.group.slug,)),
            reverse(
                "posts:profile",
                args=(self.user.username,),
            ),
        )
        for reverse_name in reverses:
            response = self.authorized_client.get(reverse_name)
            context = response.context["page_obj"]
            with self.subTest(reverse_name=reverse_name):
                self.assertIn(self.post, context, "Пост добавлен некорректно")

    def test_post_not_in_another_group(self):
        """Пост не попадает в группу, для которой не был предназначен."""

        group_2 = Group.objects.create(
            title="Тестовая группа 2",
            slug="test-slug2",
            description="Тестовое описание",
        )
        response = self.authorized_client.get(
            reverse("posts:group_list", args=(group_2.slug,))
        )
        context = response.context["page_obj"]
        self.assertNotIn(self.post, context, "Пост добавлен в другую группу")

    def test_post_detail_show_comment(self):
        """Комментарий виден на странице поста."""

        response = self.authorized_client.get(
            reverse(
                "posts:post_detail",
                args=(self.post.pk,),
            )
        )
        comment = response.context["comments"]
        self.assertIn(
            self.comment,
            comment,
            "Комментария нет на странице поста",
        )

    def test_cache(self):
        """Тестирование кэша главной страницы."""

        response = self.authorized_client.get(reverse("posts:index"))
        Post.objects.get(id=1).delete()
        new_response = self.authorized_client.get(reverse("posts:index"))
        self.assertEqual(response.content, new_response.content)
        cache.clear()
        response_after_clear = self.authorized_client.get(
            reverse("posts:index")
        )
        self.assertNotEqual(response.content, response_after_clear.content)

    def test_authorized_user_can_follow_unfollow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок.
        """

        author = User.objects.create_user(username="Автор")
        user = self.user
        self.authorized_client.get(
            reverse(
                "posts:profile_follow", kwargs={"username": author.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(user=user, author=author).exists()
        )
        self.authorized_client.get(
            reverse(
                "posts:profile_unfollow", kwargs={"username": author.username}
            )
        )
        self.assertFalse(
            Follow.objects.filter(user=user, author=author).exists()
        )

    def test_post_appears_in_feed(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан.
        """

        author = User.objects.create_user(username="Автор")
        user1 = self.user
        user2 = User.objects.create_user(username="Другой автор")
        self.authorized_client.get(
            reverse(
                "posts:profile_follow", kwargs={"username": author.username}
            )
        )
        authors1 = Follow.objects.values_list("author").filter(user=user1)
        post_list1 = Post.objects.filter(author__in=authors1)
        post1 = Post.objects.create(
            author=author,
            text="Тестовый текст",
        )
        self.assertIn(post1, post_list1)
        authors2 = Follow.objects.values_list("author").filter(user=user2)
        post_list2 = Post.objects.filter(author__in=authors2)
        self.assertNotIn(post1, post_list2)


class Paginatorself(TestCase):
    """Тестирование паджинатора."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Pushkin")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        posts = []
        for post in range(POSTS_PER_PAGE + GAP):
            posts.append(
                Post(
                    text=f"Тестовый текст {post}",
                    group=cls.group,
                    author=cls.user,
                )
            )
        Post.objects.bulk_create(posts)

    def test_correct_page_context(self):
        """Тестирование паджинатора."""

        cache.clear()
        pages = [
            reverse("posts:index"),
            reverse(
                "posts:profile",
                args=(self.user.username,),
            ),
            reverse(
                "posts:group_list",
                args=(self.group.slug,),
            ),
        ]
        for page in pages:
            response1 = self.client.get(page)
            response2 = self.client.get(page + "?page=2")
            count_posts1 = len(response1.context["page_obj"])
            count_posts2 = len(response2.context["page_obj"])
            error_name = "Неверное отображение количества постов на странице"
            self.assertEqual(
                count_posts1,
                POSTS_PER_PAGE,
                error_name,
            )
            self.assertEqual(
                count_posts2,
                GAP,
                error_name,
            )
