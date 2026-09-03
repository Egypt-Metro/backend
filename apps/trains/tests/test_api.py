# apps/trains/tests/test_api.py

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.trains.constants.choices import CARS_PER_TRAIN
from apps.trains.tests.factories import TrainFactory


class TrainAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.train = TrainFactory(train_number="TRN0001")
        self.list_url = reverse("train-api:train-list")

    def test_list_trains(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["train_number"], "TRN0001")

    def test_train_detail(self):
        url = reverse("train-api:train-detail", kwargs={"pk": self.train.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["train_number"], self.train.train_number)
        self.assertEqual(response.data["direction"], self.train.direction)

    def test_train_detail_includes_cars(self):
        # A Train's cars are created automatically by a post_save signal.
        url = reverse("train-api:train-detail", kwargs={"pk": self.train.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["cars"]), CARS_PER_TRAIN)
        self.assertEqual(response.data["cars"][0]["car_number"], 1)

    def test_create_train_requires_authentication(self):
        response = self.client.post(self.list_url, {"train_number": "TRN9999"})
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
