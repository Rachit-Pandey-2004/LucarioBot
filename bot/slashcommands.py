import hikari
import lightbulb

# Create a plugin
plugin = lightbulb.Plugin("Basic Commands")

# Ping command
@plugin.command
@lightbulb.command("ping", "Check the bot's latency")
@lightbulb.implements(lightbulb.SlashCommand)
async def ping(ctx: lightbulb.Context) -> None:
    await ctx.respond(f"Pong! Latency: {ctx.bot.heartbeat_latency * 1000:.2f}ms")

# Hello command
@plugin.command
@lightbulb.command("hello", "Says hello to you")
@lightbulb.implements(lightbulb.SlashCommand)
async def hello(ctx: lightbulb.Context) -> None:
    await ctx.respond(f"Hello, {ctx.author.username}!")

# Echo command with parameter
@plugin.command
@lightbulb.option("message", "The message to echo", type=str)
@lightbulb.command("echo", "Echoes your message")
@lightbulb.implements(lightbulb.SlashCommand)
async def echo(ctx: lightbulb.Context) -> None:
    message = ctx.options.message
    await ctx.respond(f"Echo: {message}")

# Load the plugin
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)