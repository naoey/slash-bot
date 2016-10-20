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

The bot uses the prefix `,` for all commands. If a module has listed a module prefix, the command syntax will be `,<module_prefix> <command> <parameters>`. For example, the command for League of Legends summoner information would be `,lol summoner Faker KR`. This prefix can be changed in `slash_bot/config.py`. If no module prefix is listed, simply use the command with the prefix as `,<command> <parameters>`. The parameters column lists acceptable combinations of parameters that can be given for a command. Any Discord permissions the bot may need for a command are mentioned in the description.

#### General

| Command    | Parameters                                      | Description                                                                                    |
|------------|-------------------------------------------------|------------------------------------------------------------------------------------------------|
| `stats`, `st` | | Displays some bot info.                    |

#### Administration

| Command    | Parameters                                      | Description                                                                                    |
|------------|-------------------------------------------------|------------------------------------------------------------------------------------------------|
| `slowmode`, `sm` | Optional `@<discord_user>`, `<interval_in_seconds>`, `@<discord_user> <interval_in_seconds>` | If no parameters are given, allows only 1 message per 5 seconds in the channel where it is invoked. Slow can be applied to individual users by mentioning them. If users are slowed on a channel and then slow is invoked for the whole channel, the per-user slows will be reset. **Requires 'Manage Messages' permission**.      |

#### League of Legends

Module prefix: `lol`

| Command    | Parameters                                      | Description                                                                                    |
|------------|-------------------------------------------------|------------------------------------------------------------------------------------------------|
| `setname`, `setn` | `<summoner_name> <region>` | Register your summoner name with the bot so that users can mention you/you don't have to type it in for every command.
| `summoner`, `sumn`, `player` | `@<discord_user>` or `<summoner_name> <region>` | General summoner information, including champion masteries and ranked stats for current season. |   
| `game`, `g`, `live`     | `@<discord_user>` or `<summoner_name> <region>`  | Shows current game info for summoner.                                                          |
| `runes`, `r`, `runepages`     | `@<discord_user>` or `<summoner_name> <region>`  | Show all runes pages and stats for summoner                                                  |
| `masteries`, `m`, `masterypages`     | `@<discord_user>` or `<summoner_name> <region>`  | Show all mastery pages for summoner.                                                      |
| `freechamps`, `fc`  | Optional `<region>`  | Show the free champion rotation. If `<region>` is specified, the bot queries that region otherwise assumes NA.           |

*Note that all region values must be abbreviated as per Riot's speicification (NA, EUW, EUNE etc.)*

---
SlashBot isn't meant to be a public bot because some APIs impose limits which make it unfeasible for use in a larger number of servers with many users. For best results you should host your own instance for use in your server.

SlashBot isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing League of Legends. League of Legends and Riot Games are trademarks or registered trademarks of Riot Games, Inc. League of Legends © Riot Games, Inc.
