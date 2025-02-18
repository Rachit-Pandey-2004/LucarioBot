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
                    i=0
                    for mon in data:
                        i=i+1
                        if i>=20:
                            break;
                        mon_name = mon['p_name']
                        iv = mon['iv']
                        cp = mon['cp']
                        level = mon['lvl']
                        despawn_time = int(mon['despawn_timestamp'])- (5 * 3600 + 30 * 60)  # Convert Decimal to float
                        gender = mon['gender']
                        pokemon_id = mon['id']
                        latitude, longitude = mon["latitude"], mon["longitude"]

                        # Gender symbol
                        gender_symbol = "♂️" if gender == "M" else "♀️" if gender == "F" else "❓"
                    
                        # Format despawn time
                        # Random Embed Colors
                        colors = [0x1ABC9C, 0x11806A, 0x2ECC71, 0xA84300, 0xFFD700, 0x206694, 0x71368A, 0xE91E63]
                        embed_color = random.choice(colors)

                        # Pokémon GIF (fallback to sprite)
                        gif_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/{pokemon_id}.gif"
                        static_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png"

                        embed = hikari.Embed(
                            description=(
                                f"{mon_name} {gender_symbol}\n"
                                f"**:Iv:** `{int(iv)}%`  | **:Lv:** `{level}` | **:Cp:** `{cp}`\n"
                                f"Despawns <t:{despawn_time}:R> | (<t:{despawn_time}:t>)"
                            ),
                            color=hikari.Color(embed_color),
                            timestamp=datetime.now(timezone.utc)
                        )
                        embed.set_thumbnail(gif_url)  # Attempt GIF first
                        embed.set_image(static_url)  # Fallback to static image
                        embed.add_field(name="📍 Coordinates", value=f"`{latitude}, {longitude}`", inline=False)
                        embed.set_footer(text="Lucario Bot",icon="https://cdn.discordapp.com/app-icons/1335953490568282152/1c99a8c52e2fbbecfad4ac0e1bbe882c.png?size=512")
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