import hikari
import lightbulb
from configs.configs import Config

class BotClient(lightbulb.BotApp):
    def __init__(self):
        super().__init__(
            token=Config.TOKEN,  # Enable globally
            intents=hikari.Intents.ALL
        )
        