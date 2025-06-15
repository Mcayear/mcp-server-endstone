# Economy UMoney API

Manage player economic data through Python interfaces provided by the [UMoney](https://github.com/umarurize/UMoney) plugin.

## Interface List

Accessed via:
  umoney = Plugin#server.plugin_manager.get_plugin('umoney')

Call the following methods:

1.  api_get_money_data() -> dict[str, int]
    Retrieves economic data for all players.

2.  api_get_player_money(name: str) -> int
    Retrieves the balance of a specified player.

3.  api_get_player_money_top() -> [str, int]
    Returns the [player name, balance] of the richest player.

4.  api_get_player_money_bottom() -> [str, int]
    Returns the [player name, balance] of the poorest player.

5.  api_set_player_money(name: str, amount: int) -> None
    Sets the balance of the specified player to `amount`.

6.  api_change_player_money(name: str, delta: int) -> None
    Adds `delta` to the specified player's balance (positive for increase, negative for decrease).