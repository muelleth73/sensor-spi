"""
OSC UDP client for testing
"""


class MockUDPClient:
    """
    Client that keeps the last send operation
    """

    def __init__(self):
        self.messages = []

    def send_message(self, address, payload):
        self.messages.append(
            (
                address,
                payload,
            )
        )

    def get_history(self):
        return self.messages
