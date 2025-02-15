import asyncio
import random
import hikari
import hikari.embeds
import miru
import lightbulb
from db.channel_db import Channel_Data  # Your DB handler
from db.mons_data import PGDB
from time import time
from datetime import datetime, timezone

plugin: lightbulb.BotApp  # Reference to the bot (passed from `bot.py`)
mclient: miru.Client
class RevealButton(miru.View):
    def __init__(self, coordinates: str, despawn_time: int):
        super().__init__(timeout=despawn_time - round(time()))  # Button expires on despawn
        self.coordinates = coordinates

    @miru.button(label="Reveal Location", style=hikari.ButtonStyle.PRIMARY)
    async def reveal(self, ctx: miru.ViewContext,button: miru.Button):
        """Reveals the coordinates when clicked."""
        await ctx.respond(f"📍 Coordinates: `{self.coordinates}`", flags=hikari.MessageFlag.EPHEMERAL)
        self.stop()  # Stop listening to further interactions

    async def on_timeout(self):
        """Disable button on timeout (despawn time)."""
        self.clear_items()  # Remove all buttons
        await self.message.edit(content="⏳ Pokémon has despawned!", components=[])
        
        
async def send_alerts():
    """Fetch alerts from the database and send messages automatically."""
    
    while True:
        bool_all_mons=False
        async with Channel_Data() as db:
            channelTuple = await db.get_subscribe_channel()  # Fetch Pokémon alerts from DB
            print(channelTuple)
            for channels,last_timestamp  in channelTuple:
                # print(channels," | | ",last_timestamp )#channels,last_timestamp 
                filter_dict,filter_list=await db.get_channel_filters(channelId=channels)
                current_timestamp=round(time())
                if filter_list[0]=="all":
                    bool_all_mons=True
                print(filter_dict)
                async with PGDB() as psql:
                    data= await psql.fetch_filtered_data(
                        filter_minIv=filter_dict['miniv'],
                        filter_maxIv=filter_dict['maxiv'],
                        filter_mons=filter_list,
                        filter_minCp=filter_dict['mincp'],
                        filter_maxCp=filter_dict['maxcp'],
                        filter_minLvl=filter_dict['minlvl'],
                        filter_maxLvl=filter_dict['maxlvl'],
                        filter_gender=filter_dict['gender'] ,
                        check_all_mon=bool_all_mons, 
                        last_checking_time=last_timestamp, 
                        current_checking_time=current_timestamp
                        )
                    await db.update_last_search(channels,current_timestamp)
                    for mon in data:
                        mon_name = mon['p_name']
                        iv = mon['iv']
                        cp = mon['cp']
                        level = mon['lvl']
                        despawn_time = float(mon['despawn_timestamp'])  # Convert Decimal to float
                        gender = mon['gender']
                        pokemon_id = mon['id']
                        latitude, longitude = mon["latitude"], mon["longitude"]

                        # Gender symbol
                        gender_symbol = "♂️" if gender == "M" else "♀️" if gender == "F" else "❓"
                    
                        # Format despawn time
                        despawn_readable = datetime.fromtimestamp(despawn_time, tz=timezone.utc).strftime('%H:%M:%S UTC')

                        # Random Embed Colors
                        colors = [0x1ABC9C, 0x11806A, 0x2ECC71, 0xA84300, 0xFFD700, 0x206694, 0x71368A, 0xE91E63]
                        embed_color = random.choice(colors)

                        # Pokémon GIF (fallback to sprite)
                        gif_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/{pokemon_id}.gif"
                        static_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png"

                        embed = hikari.Embed(
                            title=f"🚨 Wild {mon_name} Appeared! {gender_symbol}",
                            description=(
                                f"**IV:** `{iv}%`\n"
                                f"**CP:** `{cp}`\n"
                                f"**Level:** `{level}`\n"
                                f"**Gender:** `{gender_symbol}`"
                            ),
                            color=hikari.Color(embed_color),
                            timestamp=datetime.now(timezone.utc)
                        )
                        
                        embed.set_thumbnail(gif_url)  # Attempt GIF first
                        embed.set_image(static_url)  # Fallback to static image
                    
                        embed.add_field(
                            name="📍 Coordinates",
                            value=f"`{latitude}, {longitude}`",
                            inline=False
                        )
                        
                        embed.set_footer(text=f"🕒 Despawns at: {despawn_readable}")
                        coordinates = f"{latitude}, {longitude}"
                        #view = RevealButton(coordinates, int(despawn_time))

                        # FIX: Convert view to JSON-serializable format
                        await plugin.rest.create_message(channels, embed=embed)#, components=view.build())
                        #mclient.start_view(view)
        
        await asyncio.sleep(300)  # Wait for 5 minutes before checking again
    
# def load(bot_instance: lightbulb.BotApp):
#     """Load the alert system into the bot."""
#     global bot
#     bot = bot_instance
#     bot.create_task(send_alerts)  # Run the alert system as a background task

# def unload(_: lightbulb.BotApp):
#     """Unload the alert system (if needed)."""
#     pass
def activeAlert(bot:lightbulb.BotApp,client:miru.Client)->bool:
    global plugin, mclient
    plugin=bot
    mclient=client
    plugin.create_task(send_alerts())