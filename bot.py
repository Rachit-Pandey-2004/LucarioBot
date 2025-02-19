import hikari
import lightbulb
from configs.configs import Config
import miru
from bot.monAlert import activeAlert
bot=lightbulb.BotApp(
            token=Config.TOKEN, 
            default_enabled_guilds=[1336262785860112428,1120729950069202944],# Enable globally
            intents=hikari.Intents.ALL
        )
    
bot.load_extensions("bot.slashcommands")
bot.load_extensions("bot.ownercommands")
# bot.load_extensions("bot.monAlert")

# Simple event listener for when bot is ready

client = miru.Client(bot)
# Define a new custom View that contains 3 items
class BasicView(miru.View):

    # Define a new TextSelect menu with two options
    @miru.text_select(
        placeholder="Select me!",
        options=[
            miru.SelectOption(label="Option 1"),
            miru.SelectOption(label="Option 2"),
        ],
    )
    async def basic_select(self, ctx: miru.ViewContext, select: miru.TextSelect) -> None:
        await ctx.respond(f"You've chosen {select.values[0]}!")

    # Define a new Button with the Style of success (Green)
    @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
    async def basic_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        await ctx.respond("You clicked me!", flags=hikari.MessageFlag.EPHEMERAL)

    # Define a new Button that when pressed will stop the view
    # & invalidate all the buttons in this view
    @miru.button(label="Stop me!", style=hikari.ButtonStyle.DANGER)
    async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.stop()  # Called to stop the view

class TimeoutView(miru.View):

    @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
    async def basic_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        print("here")
        await ctx.respond("You clicked me!", flags=hikari.MessageFlag.EPHEMERAL)

    async def on_timeout(self) -> None:
        print("This view timed out!")
        # Run custom logic here  
@bot.command()
@lightbulb.command("name", "description", auto_defer=False)
@lightbulb.implements(lightbulb.SlashCommand)
async def some_slash_command(ctx: lightbulb.SlashContext) -> None:
    # Create a new instance of our view
    view = TimeoutView(timeout=120)
    await ctx.respond("Hello miru!", components=view)

    # Assign the view to the client and start it
    client.start_view(view)       
        
@bot.listen(hikari.StartedEvent)
async def on_ready(event):
    print("Bot is ready!")
    activeAlert(bot,client)
@bot.listen(lightbulb.CommandErrorEvent)
async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.CheckFailure):
        await event.context.respond("❌ You are not authorized to use this command!", flags=hikari.MessageFlag.EPHEMERAL)
# Run the bot
def run():
    bot.run()


if __name__ == "__main__":
    run()