# apps/trains/tests/test_websocket.py

from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase

from apps.stations.models import Line
from apps.trains.constants.choices import Direction, TrainStatus
from apps.trains.models import Train
from apps.trains.routing import websocket_urlpatterns

# Route through the URLRouter so ``scope["url_route"]["kwargs"]`` is populated,
# exactly as it is in production via ``metro.asgi``.
application = URLRouter(websocket_urlpatterns)


class TrainWebsocketTests(TransactionTestCase):
    def setUp(self):
        self.line = Line.objects.create(name="Line 1", color_code="#FF0000")
        self.train = Train.objects.create(
            train_number="TEST123",
            line=self.line,
            status=TrainStatus.IN_SERVICE,
            direction=Direction.HELWAN,
        )

    async def test_connects_for_existing_train_and_receives_initial_data(self):
        communicator = WebsocketCommunicator(application, "/ws/train/TEST123/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "initial_data")
        self.assertEqual(response["data"]["train_number"], "TEST123")

        await communicator.disconnect()

    async def test_rejects_connection_for_unknown_train(self):
        communicator = WebsocketCommunicator(application, "/ws/train/DOES_NOT_EXIST/")
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()

    async def test_status_request_returns_current_status(self):
        communicator = WebsocketCommunicator(application, "/ws/train/TEST123/")
        await communicator.connect()
        await communicator.receive_json_from()  # drain initial_data

        await communicator.send_json_to({"type": "request_status", "data": {}})
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "status_update")
        self.assertEqual(response["data"]["train_number"], "TEST123")

        await communicator.disconnect()
