# apps/trains/tests/test_websocket.py
from channels.testing import WebsocketCommunicator
from django.test import TestCase

from apps.trains.consumers import TrainConsumer


class TrainWebsocketTests(TestCase):
    async def test_websocket_connection(self):
        communicator = WebsocketCommunicator(TrainConsumer.as_asgi(), "/ws/train/test_train_id/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()
