import hikari
import lightbulb
from db.channel_db import Channel_Data
import asyncio

# Create a plugin
plugin = lightbulb.Plugin("Owner Level Commands",default_enabled_guilds=[1336262785860112428])

# at present implementing level hardcoded later w'll add using db
def ck_lvl(ctx:lightbulb.Context)->bool:
    if not ctx.author.id==1283465824103043072:
        # await ctx.respond("❌ unAuthorized ...")
        return False
    else:
        return True
async def insert_config(guildId: int, channelId: int, minIv: int, maxIv: int, minCp: int, maxCp: int, minLvl: int, maxLvl: int, gender: str, pokemon_list: list):
    async with Channel_Data() as cd:
        # guildId: int, channelId: int, minIv: int, maxIv: int, minCp: int, maxCp: int, minLvl: int, maxLvl: int, gender: str, pokemon_list: list
        await cd.insert_channel_data(guildId, channelId, minIv, maxIv, minCp, maxCp, minLvl, maxLvl, gender, pokemon_list)
    pass
# Echo command with parameter
VALID_POKEMON = {"mewtwo", "rayquaza", "groudon", "kyogre", "dialga", "palkia", "all"}


@plugin.command
@lightbulb.add_checks(lightbulb.Check(ck_lvl))
@lightbulb.option("channel", "The message to echo",type=hikari.TextableGuildChannel,  required=True)
@lightbulb.option("min_iv",'set miniv (0 to 100)',type=int,min_value=0,max_value=100,default=-1)
@lightbulb.option("max_iv",'set maxiv (0 to 100)',type=int,min_value=0,max_value=100,default=100)
@lightbulb.option("min_cp",'set mincp f',type=int,default=-1)
@lightbulb.option("max_cp",'set maxcp f',type=int,default=10000)
@lightbulb.option("min_lvl",'set minlvl ',type=int,default=-1)
@lightbulb.option("max_lvl",'set maxlvl ',type=int,default=50)
@lightbulb.option("gender","set a M N F A[all]", type=str,default='A')
@lightbulb.option("pokemon","Enter Pokémon names (comma-separated, or 'ALL')",required=False,type=str,default='ALL')
@lightbulb.command("pokeset", "subscribe channel")
@lightbulb.implements(lightbulb.SlashCommand)
async def pokeset(ctx: lightbulb.Context) -> None:
    print("---here---")
    try:
        pokemon = ctx.options.pokemon.lower()
        if pokemon:
            selected_pokemon = [p.strip() for p in pokemon.split(",") if p.strip()]
            # Validate Pokémon names
            selected_pokemon = [p for p in selected_pokemon if p in VALID_POKEMON]
            if not selected_pokemon:
                # selected_pokemon = ["ALL"]  # If all names are invalid, default to ALL
                await ctx.respond(f"{pokemon} is a invalid entry")
                return 
        else:
            selected_pokemon = ["ALL"]
        print(selected_pokemon)
        await insert_config(
            ctx.guild_id,
            ctx.options.channel,
            ctx.options.min_iv,
            ctx.options.max_iv,
            ctx.options.min_cp,
            ctx.options.max_cp,
            ctx.options.min_lvl,
            ctx.options.max_lvl,
            ctx.options.gender.upper(),
            selected_pokemon
            )
        await ctx.respond(f"Echo: {ctx.options.channel}", flags=hikari.MessageFlag.EPHEMERAL)
    except lightbulb.errors.CheckFailure:
        await ctx.respond("‼️ There is a failure...", flags=hikari.MessageFlag.EPHEMERAL)

# Load the plugin
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)