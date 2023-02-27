import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTest(TestCase):
    """Тестирование форм."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Pushkin")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
        )
        cls.post = Post.objects.create(
            text="Тестовый пост", author=cls.user, group=cls.group
        )
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""

        posts_count = Post.objects.count()
        form_data = {
            "text": "Новый пост",
            "group": self.group.pk,
            "image": self.uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse("posts:profile", args=(self.user.username,)),
        )
        self.assertEqual(
            Post.objects.count(), posts_count + 1, "Запись не добавлена"
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK, "Страница недоступна"
        )
        self.assertTrue(
            Post.objects.filter(
                text="Новый пост", group=self.group.pk, image="posts/small.gif"
            ).exists(),
            "Запись не добавлена",
        )

    def test_post_edit(self):
        """Валидная форма редактирует запись в Post."""

        old_text = self.post
        posts_count = Post.objects.count()
        group2 = Group.objects.create(title="Тестовая группа2", slug="slug-2")
        form_data = {"text": "Редактированный пост", "group": group2.id}
        response = self.authorized_client.post(
            reverse(
                "posts:post_edit",
                args=(self.post.pk,),
            ),
            data=form_data,
            follow=True,
        )
        self.assertTrue(
            Post.objects.filter(
                text="Редактированный пост", group=group2.id
            ).exists(),
            "Запись не редактируется",
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK, "Страница недоступна"
        )
        self.assertEqual(
            Post.objects.count(),
            posts_count,
            "Пост не редактируется, а создает новый",
        )
        self.assertNotEqual(
            old_text.text,
            form_data["text"],
            "Пользователь не может изменить содержание поста",
        )
        self.assertNotEqual(
            old_text.group,
            form_data["group"],
            "Пользователь не может изменить группу поста",
        )

    def test_group_null(self):
        """Проверка, что группу можно не указывать"""

        old_text = self.post
        form_data = {"text": "Редактированный пост", "group": ""}
        response = self.authorized_client.post(
            reverse("posts:post_edit", args=(self.post.pk,)),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(
            old_text.group,
            form_data["group"],
            "Пользователь не может оставить группу пустым",
        )

    def test_guest_client_cant_create_edit_post(self):
        """Неавторизованный клиент не может создать/редактировать пост"""

        posts_count = Post.objects.count()
        urls = (
            reverse(
                "posts:post_edit",
                args=(self.post.pk,),
            ),
            reverse("posts:post_create"),
        )
        login = reverse("users:login")
        for url in urls:
            with self.subTest(url=url):
                response = self.client.post(url, data={"text": "Чужой пост"})
                self.assertNotEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    "Неавторизованный пользователь может создать/"
                    " редактировать пост",
                )
                self.assertRedirects(response, f"{login}?next={url}")
                self.assertNotEqual(
                    Post.objects.count(),
                    posts_count + 1,
                    "Пост добавлен по ошибке неавторизованным пользователем",
                )

    def test_comment_auth_client(self):
        """Комментировать посты может только авторизованный пользователь"""

        comment_count = Comment.objects.count()
        self.client.post(
            reverse("posts:add_comment", args=(self.post.pk,)),
            data={"text": "Тестовый комментарий"},
            follow=True,
        )
        self.assertEqual(
            Comment.objects.count(),
            comment_count,
            "Неавторизованный пользователь может добавить комментарий",
        )
        response_auth = self.authorized_client.post(
            reverse("posts:add_comment", args=(self.post.pk,)),
            data={"text": "Тестовый комментарий"},
            follow=True,
        )
        self.assertEqual(
            response_auth.status_code,
            HTTPStatus.OK,
            "Страница недоступна",
        )
        self.assertRedirects(
            response_auth, reverse("posts:post_detail", args=(self.post.pk,))
        )
        self.assertEqual(
            Comment.objects.count(),
            comment_count + 1,
            "Авторизованный пользователь не может добавить комментарий",
        )
