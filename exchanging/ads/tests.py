from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from ads.models import Ad, ExchangeProposal
from django.urls import reverse

class APITests(APITestCase):
    def setUp(self):
        # Инициализация тестового клиента
        self.client = APIClient()

        # Создаем тестовых пользователей
        self.user1 = User.objects.create_user(
            username='user1', email='user1@example.com', password='password123'
        )
        self.user2 = User.objects.create_user(
            username='user2', email='user2@example.com', password='password123'
        )

        # Создаем токены для пользователей
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

        # Создаем тестовые объявления
        self.ad1 = Ad.objects.create(
            user=self.user1,
            title='Книга',
            description='Хорошая книга',
            category='Книги',
            condition='Новое',
            image_url='http://example.com/image1.jpg'
        )
        self.ad2 = Ad.objects.create(
            user=self.user2,
            title='Ноутбук',
            description='Мощный ноутбук',
            category='Электроника',
            condition='Б/У',
            image_url='http://example.com/image2.jpg'
        )

        # Создаем тестовое предложение обмена
        self.proposal = ExchangeProposal.objects.create(
            ad_sender=self.ad1,
            ad_receiver=self.ad2,
            comment='Хочу обменять книгу на ноутбук',
            status='pending'
        )

    # Тесты для /register
    def test_register_success(self):
        """Тестируем успешную регистрацию пользователя."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123'
        }
        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'newuser')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_missing_fields(self):
        """Тестируем регистрацию с отсутствующими полями."""
        data = {'username': 'newuser'}  # Отсутствуют email и password
        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)

    def test_register_duplicate_username(self):
        """Тестируем регистрацию с уже существующим именем пользователя."""
        data = {
            'username': 'user1',  # Уже существует
            'email': 'newemail@example.com',
            'password': 'password123'
        }
        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    # Тесты для /login
    def test_login_success(self):
        """Тестируем успешную авторизацию."""
        data = {'username': 'user1', 'password': 'password123'}
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['token'], self.token1.key)

    def test_login_invalid_credentials(self):
        """Тестируем авторизацию с неверными данными."""
        data = {'username': 'user1', 'password': 'wrongpassword'}
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    # Тесты для /api/ads/
    def test_get_ads_list_unauthenticated(self):
        """Тестируем получение списка объявлений без авторизации."""
        response = self.client.get(reverse('ad-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)  # Два объявления
        self.assertEqual(response.data['count'], 2)

    def test_get_ads_list_pagination(self):
        """Тестируем пагинацию для списка объявлений."""
        # Создаем дополнительные объявления, чтобы проверить пагинацию
        for i in range(15):
            Ad.objects.create(
                user=self.user1,
                title=f'Книга {i}',
                description=f'Описание книги {i}',
                category='Книги',
                condition='Новое'
            )
        response = self.client.get(reverse('ad-list') + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 7)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)

    def test_get_ads_filter_by_category(self):
        """Тестируем фильтрацию по категории (без учета регистра)."""
        response = self.client.get(reverse('ad-list') + '?category=Книги')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['category'], 'Книги')

    def test_get_ads_search(self):
        """Тестируем поиск по title и description (без учета регистра)."""
        response = self.client.get(reverse('ad-list') + '?search=Книга')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Книга')

    def test_create_ad_authenticated(self):
        """Тестируем создание объявления с авторизацией."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        data = {
            'title': 'Новая книга',
            'description': 'Описание новой книги',
            'category': 'Книги',
            'condition': 'Новое',
            'image_url': 'http://example.com/image3.jpg'
        }
        response = self.client.post(reverse('ad-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Новая книга')
        self.assertEqual(Ad.objects.count(), 3)

    def test_create_ad_unauthenticated(self):
        """Тестируем создание объявления без авторизации."""
        data = {
            'title': 'Новая книга',
            'description': 'Описание новой книги',
            'category': 'Книги',
            'condition': 'Новое'
        }
        response = self.client.post(reverse('ad-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_ad_owner(self):
        """Тестируем обновление своего объявления."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        data = {'title': 'Обновленная книга'}
        response = self.client.patch(reverse('ad-detail', args=[self.ad1.ad_id]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Обновленная книга')

    def test_update_ad_not_owner(self):
        """Тестируем попытку обновления чужого объявления."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        data = {'title': 'Обновленная книга'}
        response = self.client.patch(reverse('ad-detail', args=[self.ad1.ad_id]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_ad_owner(self):
        """Тестируем удаление своего объявления."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.delete(reverse('ad-detail', args=[self.ad1.ad_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ad.objects.filter(ad_id=self.ad1.ad_id).exists())

    def test_delete_ad_not_owner(self):
        """Тестируем попытку удаления чужого объявления."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        response = self.client.delete(reverse('ad-detail', args=[self.ad1.ad_id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_exchange_list_authenticated(self):
        """Тестируем получение списка предложений обмена для авторизованного пользователя."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.get(reverse('exchangeproposal-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['exchange_id'], self.proposal.exchange_id)
        self.assertNotIn('next', response.data)

    def test_get_exchange_list_unauthenticated(self):
        """Тестируем получение списка предложений без авторизации."""
        response = self.client.get(reverse('exchangeproposal-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_exchange_filter_by_status(self):
        """Тестируем фильтрацию предложений по статусу (без учета регистра)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.get(reverse('exchangeproposal-list') + '?status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'pending')

    def test_create_exchange_proposal_authenticated(self):
        """Тестируем создание предложения обмена."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        data = {
            'ad_sender_id': self.ad1.ad_id,
            'ad_receiver_id': self.ad2.ad_id,
            'comment': 'Новое предложение'
        }
        response = self.client.post(reverse('exchangeproposal-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['comment'], 'Новое предложение')
        self.assertEqual(ExchangeProposal.objects.count(), 2)

    def test_create_exchange_proposal_same_ad(self):
        """Тестируем попытку создания предложения с одинаковыми объявлениями."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        data = {
            'ad_sender_id': self.ad1.ad_id,
            'ad_receiver_id': self.ad1.ad_id,
            'comment': 'Нельзя обменять на себя'
        }
        response = self.client.post(reverse('exchangeproposal-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Нельзя обмениваться с самим собой', str(response.data))

    def test_create_exchange_proposal_not_owner(self):
        """Тестируем попытку создания предложения с чужим объявлением."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        data = {
            'ad_sender_id': self.ad1.ad_id,  # Чужое объявление
            'ad_receiver_id': self.ad2.ad_id,
            'comment': 'Чужое объявление'
        }
        response = self.client.post(reverse('exchangeproposal-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Вы можете предлагать только свои объявления', str(response.data))

    def test_update_exchange_proposal_status_accepted(self):
        """Тестируем обновление статуса предложения на 'accepted'."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')  # Получатель
        data = {'status': 'accepted'}
        response = self.client.patch(
            reverse('exchangeproposal-detail', args=[self.proposal.exchange_id]),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'accepted')
        self.assertFalse(Ad.objects.filter(ad_id=self.ad1.ad_id).exists())
        self.assertFalse(Ad.objects.filter(ad_id=self.ad2.ad_id).exists())

    def test_update_exchange_proposal_invalid_status(self):
        """Тестируем попытку обновления с недопустимым статусом."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        data = {'status': 'invalid_status'}
        response = self.client.patch(
            reverse('exchangeproposal-detail', args=[self.proposal.exchange_id]),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is not a valid choice', str(response.data))

    def test_update_exchange_proposal_not_status(self):
        """Тестируем попытку обновления не поля status."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        data = {'comment': 'Новый комментарий'}
        response = self.client.patch(
            reverse('exchangeproposal-detail', args=[self.proposal.exchange_id]),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Можно обновлять только поле 'status'", str(response.data))

    def test_delete_exchange_proposal_owner(self):
        """Тестируем удаление своего предложения обмена."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.delete(
            reverse('exchangeproposal-detail', args=[self.proposal.exchange_id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ExchangeProposal.objects.filter(exchange_id=self.proposal.exchange_id).exists())

    def test_delete_exchange_proposal_not_owner(self):
        """Тестируем попытку удаления чужого предложения."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        response = self.client.delete(
            reverse('exchangeproposal-detail', args=[self.proposal.exchange_id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('You do not have permission to perform this action', str(response.data))
        