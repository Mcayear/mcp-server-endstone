# Register event listeners

Endstone provides a powerful event system that allows plugins to listen to various events that happen in the
server. Let's walk you through registering a simple event listener.

## Add event handlers

Let's say your plugin want to listen to when a player joins the server and send a message to inform everyone on the
server.

``` python title="src/endstone_my_plugin/my_plugin.py" linenums="1" hl_lines="1-2 13-16"
from endstone import ColorFormat
from endstone.event import event_handler, PlayerJoinEvent
from endstone.plugin import Plugin

class MyPlugin(Plugin):
    api_version = "0.5"

    # ...

    def on_enable(self) -> None:
        self.logger.info("on_enable is called!")

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent):
        self.server.broadcast_message(ColorFormat.YELLOW + f"{event.player.name} has joined the server")
```

## Register listeners

Now, we need to register our event handlers to the Endstone event system.

``` python title="src/endstone_my_plugin/my_plugin.py" linenums="1" hl_lines="12"
from endstone import ColorFormat
from endstone.event import event_handler, PlayerJoinEvent
from endstone.plugin import Plugin

class MyPlugin(Plugin):
    api_version = "0.5"

    # ...

    def on_enable(self) -> None:
        self.logger.info("on_enable is called!")
        self.register_events(self)

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent):
        self.server.broadcast_message(ColorFormat.YELLOW + f"{event.player.name} has joined the server")
```

By calling `self.register_events`, Endstone will look into the object that is passed in as the argument and
register all handlers with a `@event_handler` decorator to the event system.