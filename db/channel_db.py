'''
HERE when passing mons list to a filter ALL at index 0 when list size is 1 means that all monsters are subscribed so check then only
'''
from time import time
import asyncio
from asyncpg import create_pool, exceptions
from configparser import ConfigParser
from os import getcwd
from asyncpg.exceptions import UniqueViolationError
class Channel_Data:
    def __init__(self, filename="%s/db/config.ini" % getcwd(), section="postgresql") -> None:
        parser = ConfigParser()
        parser.read(filename)
        self.db_config = {}
        if parser.has_section(section):
            parms = parser.items(section)
            for items in parms:
                self.db_config[items[0]] = items[1]
        else:
            raise Exception("Section {0} not found in the {1} file".format(section, filename))

    async def __aenter__(self):
        connection_successful = await self.__Stablish_Connection()
        if connection_successful:
            table_created = await self.__generate_tables()  # Ensure tables are created
            if not table_created:
                raise Exception("Failed - Table generation sequence did not execute.")
            return self
        raise Exception("Failed! No connection was established with the database")

    async def __aexit__(self, exc_type, exc_value, traceback):
        if hasattr(self, 'pool') and self.pool:
            await self.pool.close()

    async def __Stablish_Connection(self) -> bool:
        print("Establishing database connection...")
        try:
            self.pool = await create_pool(
                host=self.db_config["hostname"],
                port=self.db_config["port_number"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                database=self.db_config["database"],
                min_size=10,
                max_size=20,
                command_timeout=10,
                max_inactive_connection_lifetime=5
            )
            print("Database connection established successfully!")
            return True
        except exceptions.InvalidAuthorizationSpecificationError:
            print("Invalid user: {0}".format(self.db_config["user"]))
        except exceptions.InvalidPasswordError:
            print("Incorrect password for user {0}".format(self.db_config["user"]))
        except exceptions.InvalidCatalogNameError:
            print("Database does not exist")
        except Exception as error:
            print("Error during establishing the connection:\n{0}".format(error))
        return False

    async def __generate_tables(self):
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():  # Ensure commit
                    print("Creating tables if not exist...")
                    await conn.execute(
                        """--sql
                        CREATE TABLE IF NOT EXISTS channel_registry (
                            guildId BIGINT NOT NULL,
                            channelId BIGINT NOT NULL UNIQUE,
                            lastCheckTime BIGINT NOT NULL,
                            PRIMARY KEY (guildId, channelId)
                        );
                        CREATE TABLE IF NOT EXISTS channel_mons_config (
                            guildId BIGINT NOT NULL,
                            channelId BIGINT NOT NULL UNIQUE,
                            minIv INT NOT NULL CHECK (minIv >= -1 AND minIv <= 100),
                            maxIv INT NOT NULL CHECK (maxIv >= -1 AND maxIv <= 100),
                            minCp INT NOT NULL CHECK (minCp >= -1) DEFAULT -1,
                            maxCp INT NOT NULL DEFAULT -1,
                            minLvl INT NOT NULL CHECK (minLvl >= -1) DEFAULT -1,
                            maxLvl INT NOT NULL CHECK (maxLvl >= -1) DEFAULT -1,
                            gender VARCHAR(1) NOT NULL CHECK (gender IN ('M', 'F', 'N', 'A')),
                            PRIMARY KEY (guildId, channelId),
                            FOREIGN KEY (guildId, channelId) REFERENCES channel_registry (guildId, channelId) ON DELETE CASCADE
                        );
                        CREATE TABLE IF NOT EXISTS channel_pokemon_filters (
                            guildId BIGINT NOT NULL,
                            channelId BIGINT NOT NULL ,
                            pokemon VARCHAR(50) NOT NULL,
                            PRIMARY KEY (guildId, channelId, pokemon),
                            FOREIGN KEY (guildId, channelId) REFERENCES channel_registry (guildId, channelId) ON DELETE CASCADE
                        );
                        """
                    )
                    print("Tables created successfully!")
            return True
        except Exception as e:
            print(f"Failed to create tables: {e}")
            return False



    async def insert_channel_data(self, guildId: int, channelId: int, minIv: int, maxIv: int, minCp: int, maxCp: int, minLvl: int, maxLvl: int, gender: str, pokemon_list: list):
        """
        Inserts channel filter settings and multiple Pokémon filters into the database.
        Prevents duplicate channelId using a UNIQUE constraint in the database.
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    try:
                        # Insert into registry (ensure channel exists)
                        await conn.execute(
                            '''
                            INSERT INTO channel_registry (guildId, channelId,lastCheckTime)
                            VALUES ($1, $2, $3);
                            ''',
                            guildId, channelId, round(time())
                        )
                    except UniqueViolationError as e:
                        print(f"⚠️ Error: channelId {channelId} is already registered under another guild. Cannot register in guild {guildId}.\n{e}")
                        return False
    
                    # Insert channel configuration
                    await conn.execute(
                        '''
                        INSERT INTO channel_mons_config (guildId, channelId, minIv, maxIv, minCp, maxCp, minLvl, maxLvl, gender)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (guildId, channelId) DO UPDATE
                        SET minIv = EXCLUDED.minIv, maxIv = EXCLUDED.maxIv, minCp = EXCLUDED.minCp, 
                            maxCp = EXCLUDED.maxCp, minLvl = EXCLUDED.minLvl, maxLvl = EXCLUDED.maxLvl, gender = EXCLUDED.gender;
                        ''',
                        guildId, channelId, minIv, maxIv, minCp, maxCp, minLvl, maxLvl, gender
                    )
    
                    # Insert Pokémon filters
                    await conn.execute(
                        '''
                        DELETE FROM channel_pokemon_filters WHERE guildId = $1 AND channelId = $2;
                        ''', guildId, channelId
                    )
    
                    for pokemon in pokemon_list:
                        await conn.execute(
                            '''
                            INSERT INTO channel_pokemon_filters (guildId, channelId, pokemon)
                            VALUES ($1, $2, $3);
                            ''',
                            guildId, channelId, pokemon
                        )
    
                print(f"✅ Successfully added channel {channelId} with filters for {len(pokemon_list)} Pokémon.")
                return True
    
        except Exception as e:
            print(f"❌ Error inserting channel data: {e}")
            return False

    async def update_last_search(self,channelId:int,ts:int)->bool:
        """
        Update the timestamp when last notification was posted on that channnel
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""--sql
                UPDATE channel_registry  
                SET lastCheckTime=$1 
                WHERE channelId=$2               
                """,
                ts,channelId
                )
                return True
        except exceptions as e:
            print(e)
            return False
    
        pass

    async def unsubscribe_channel(self, guildId: int, channelId: int):
        """
        Deletes a channel's configuration and filters from all related tables.
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Delete all related data and check if deletion occurred
                    await conn.execute(
                        "DELETE FROM channel_pokemon_filters WHERE guildId = $1 AND channelId = $2 RETURNING *;",
                        guildId, channelId
                    )
                    await conn.execute(
                        "DELETE FROM channel_mons_config WHERE guildId = $1 AND channelId = $2 RETURNING *;",
                        guildId, channelId
                    )
                    delete_channel = await conn.execute(
                        "DELETE FROM channel_registry WHERE guildId = $1 AND channelId = $2 RETURNING *;",
                        guildId, channelId
                    )
                    # Check if the channel was actually deleted
                    if delete_channel:
                        print(f"🗑️ Successfully unsubscribed channel {channelId} from guild {guildId}.")
                        return True
                    else:
                        print(f"⚠️ Channel {channelId} was not found in guild {guildId}, nothing was deleted.")
                        return False
    
        except Exception as e:
            print(f"❌ Failed to unsubscribe channel: {e}")
            return False
    async def get_subscribe_channel(self,guild=None,channel=None):
        """
        planned use case is for getting the channel list and last time the alert was sent
        """
        try:
            async with self.pool.acquire() as conn:
                if not guild and not channel:
                    query="SELECT channelid, lastCheckTime FROM channel_registry;"
                    data=await conn.fetch(query)
                else:
                    query = "SELECT channelid, lastCheckTime FROM channel_registry WHERE guildid = $1 AND channelid = $2;"
                    data=await conn.fetchrow(query, guild, channel)
                return data
        except exceptions as e:
            print("error has been hit -> ",e)
    async def get_channel_filters(self, channelId: int):
        """
        Retrieves filter settings and Pokémon for a specific channel.
        """
        try:
            async with self.pool.acquire() as conn:
                filters = await conn.fetchrow(
                    '''
                    SELECT * FROM channel_mons_config WHERE channelId = $1;
                    ''',
                    channelId
                )
                if not filters:
                    return None

                pokemons = await conn.fetch(
                    '''
                    SELECT pokemon FROM channel_pokemon_filters WHERE channelId = $1;
                    ''',channelId
                )

                pokemon_list = [p['pokemon'] for p in pokemons]
                return dict(filters), pokemon_list

        except Exception as e:
            print(f"Error fetching channel filters: {e}")
            return None

# Example usage:
async def main():
    async with Channel_Data() as db:
        # await db.insert_channel_data(789, 457, 80, 95, -1, 1500, -1, 30, 'F', ['Pikachu'])
        # filters, pokemons = await db.get_channel_filters(789, 457)
        # print("Channel Filters:", filters)
        # print("Subscribed Pokémon:", pokemons)
        # await db.unsubscribe_channel(123, 456)
        pass

# if __name__ == "__main__":
#     asyncio.run(main())
