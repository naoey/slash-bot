### SlashBot
---
A chatbot for Discord
A chatbot currently focusing on bringing as much information about your games as possible to Discord.

#### Setting up
* Install Python 3.5
* Clone the repository
* Set the paths to your credentials files (JSON) in `slash_bot/config.py`
* Open a terminal or command prompt and `cd` into the cloned repository
* `$ pip install -r requirements.txt`
* On macOS or Linux `$ ./run.sh`
* On Windows `> cd slash_bot && python core.py && cd ..`

*The Discord credentials are mandatory, other required credentials depend on your activated modules.*

Example discord.json credentials file:
```json
{
  "token":"xxxxxxxxxxxxxxxxxxxxx",
  "client_id":"xxxxxxxxxxxxxxxxxxxxx",
  "bot_id":"xxxxxxxxxxxxxxxxxxxxx",
  "owner_id":"xxxxxxxxxxxxxxxxxxxxx",
  "server_id":"xxxxxxxxxxxxxxxxxxxxx",
  "log_channel_id":"xxxxxxxxxxxxxxxxxxxxx",
  "invite_link": "https://discordapp.com/oauth2/authorize?&client_id=<your_client_id>&scope=bot"
}
```

The `token` value is mandatory. The remaining values are optional and are currently not used anywhere. The `server_id` refers to the bot's server, if it has one. `log_channel_id` will eventually be used for optional information and status logging to a Discord text channel.

Example rito.json credentials file:
```json
{
    "api_key": "xxxxxxxxxxxxxxxxxxxxx"
}
```
----
### Commands

The bot uses the prefix `,` for all commands. The command syntax is `,<module_prefix> <module_command> <arguments>`. For example, the command for League of Legends summoner information would be `,lol summoner Faker KR`. This prefix can be changed in `slash_bot/config.py`

#### League of Legends

Module prefix: `lol`

| Command    | Parameters                                      | Description                                                                                    |
|------------|-------------------------------------------------|------------------------------------------------------------------------------------------------|
| `summoner` | `@<discord_user>` or `<summoner_name> <region>` | General summoner information, including champion masteries and ranked stats for current season |   
| `game`     | `@<discord_user>` or `<summoner_name> <region>`  | Shows current game info for summoner                                                          |
| `runes`     | `@<discord_user>` or `<summoner_name> <region>`  | Show all runes pages and stats for summoner                                                  |
| `masteries`     | `@<discord_user>` or `<summoner_name> <region>`  | Show all mastery pages for summoner                                                      |
| `freechamps`  | Optional `<region>`  | Show the free champion rotation. If `<region>` is specified, the bot queries that region otherwise assumes NA           |

*Note that all region values must be abbreviated as per Riot's speicification (NA, EUW, EUNE etc.)*

---
SlashBot isn't meant to be a public bot because some APIs impose limits which make it unfeasible for use in a larger number of servers with many users. For best results you should host your own instance for use in your server.

SlashBot isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing League of Legends. League of Legends and Riot Games are trademarks or registered trademarks of Riot Games, Inc. League of Legends © Riot Games, Inc.
