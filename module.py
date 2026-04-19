"""
file: module.py
description: A web server module for the Python Actor Framework (PAF). It includes a basic structure for handling messages and performing background tasks.
author: Your Name (your.email@example.com)
"""

from time import sleep
from typing import Optional
from paf.communication import Message, Protocol, Module

class WebServer(Module):
    """
    A web server module for the PAF framework.
    """

    def __init__(self, address: str, protocol: Protocol, debug: Optional[int] = 0):
        """Initialises the module and sets up the protocol.

        Args:
            address (str): The address of the module.
            protocol (Protocol): The protocol instance.
            debug (Optional[int]): Debug level (default is 0)."""
        self.debug = debug
        super().__init__(address, protocol)

    def handle_message(self, message: Message) -> bool:
        """Handle incoming messages.

        Args:
            message (Message): The message to handle.

        Returns:
            bool: True if the module should shutdown, False otherwise.
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling message: {message}")
        if message.command == "custom_action":
            return self.message_custom_action(message)
        return super().handle_message(message)
        
    def background_task(self):
        while self.background_task_running:
            if self.debug: print(f"{self.__class__.__name__} ({self.address}): Running background task.")
            # Perform background task here
            sleep(1)

    def message_custom_action(self, message: Message) -> bool:
        """Handles the "custom_action" message

        Args:
            message (Message): Incoming message to handle

        Returns:
            bool: False to indicate that the module should continue running after handling the message
        """
        if self.debug: print(f"{self.__class__.__name__} ({self.address}): Handling custom action message: {message}")
        # Perform custom action here
        return False