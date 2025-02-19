# apps/trains/tests/test_api.py

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import sys
import os

from apps.trains.tests.factories import TrainFactory
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))


class TrainAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.train = TrainFactory()
        self.url = reverse('train-list')

    def test_list_trains(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_train_detail(self):
        url = reverse('train-detail', kwargs={'pk': self.train.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['train_id'], self.train.train_id)
