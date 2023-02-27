from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class URLTests(TestCase):
    """Тестирование URL."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Pushkin")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
        )

        cls.reverse_templates_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", args=(cls.group.slug,)
            ): "posts/group_list.html",
            reverse(
                "posts:profile",
                args=(cls.user.username,),
            ): "posts/profile.html",
            reverse(
                "posts:post_detail",
                args=(cls.post.pk,),
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit",
                args=(cls.post.pk,),
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_url_exists_at_desired_location(self):
        """Проверка общедоступных страницы."""

        for url in self.reverse_templates_names:
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)
                global error_name
                error_name = f"Нет доступа к странице {url}"
                self.assertEqual(
                    response.status_code, HTTPStatus.OK, error_name
                )

    def test_url_exists_for_authorized_client(self):
        """Страницы доступны авторизованным пользователям."""

        for url in self.reverse_templates_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK, error_name
                )

    def test_url_exists_for_author(self):
        """Страница /posts/<post_id>/edit/ доступна только автору поста."""

        user = User.objects.create_user(username="Lermontov")
        authorized_client = Client()
        authorized_client.force_login(user)
        response = authorized_client.get(
            reverse(
                "posts:post_edit",
                args=(self.post.pk,),
            )
        )
        self.assertNotEqual(
            response.status_code,
            HTTPStatus.OK,
            "Чужак пытается отредактировать пост",
        )

    def test_url_redirect_anonymous_on_auth_login(self):
        """Страницы для неавторизованного пользователя перенаправят анонимного
        пользователя на страницу логина.
        """

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
                response = self.client.get(url, follow=True)
                self.assertRedirects(response, f"{login}?next={url}")

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        cache.clear()
        for address, template in self.reverse_templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f"{address} не соответствует шаблону {template}",
                )

    def test_unexisting_page(self):
        """Запрос к несуществующей странице."""

        response = self.client.get("/unexisting_page/")
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            "Ошибка запроса к несуществующей странице",
        )
