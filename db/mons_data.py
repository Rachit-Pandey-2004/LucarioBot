import asyncio
from asyncpg import exceptions, create_pool
from socket import gaierror
from configparser import ConfigParser
from os import getcwd
from time import time

class PGDB:

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

            return self

        raise Exception("Failed! no connection was stablished with the database")
        pass

    async def __aexit__(self, exc_type, exc_value, traceback):
        if hasattr(self, 'pool') and self.pool:
            await self.pool.close()
        pass

    async def __Stablish_Connection(self) -> bool:
        # for stablishing pool connection
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
            print("new connection to db was stablished successfully")

            return True

        except exceptions.InvalidAuthorizationSpecificationError:
            print("{0} dosen't exists".format(self.db_config["user"]))
        except exceptions.InvalidPasswordError:
            print("wrong password for the user {1}".format(self.db_config["user"]))
        except exceptions.InvalidCatalogNameError:
            print("database dosen't exists")
        except gaierror:
            print("Invalid host")
        except OSError:
            print("Connection failed might be due to port number")
        except ValueError:
            print("wrong format for port number")
        except Exception as error:
            print("Error during stablishing the connection\n{0}".format(error))
        return False

    async def fetch_filtered_data(
        self, 
        filter_minIv: int, 
        filter_maxIv: int,
        filter_minCp:int,
        filter_maxCp:int,
        filter_minLvl:int,
        filter_maxLvl:int,
        filter_gender:str ,
        filter_mons: list,
        last_checking_time:time=None, 
        current_checking_time:time=None
        ):
        print(filter_gender)
        try:
            async with self.pool.acquire() as conn:

                query = """
                SELECT id, p_name, cp,lvl,gender,iv, ST_Y(coordinates::geometry) AS latitude, ST_X(coordinates::geometry) AS longitude,
                EXTRACT(EPOCH FROM despawn) AS despawn_timestamp, created
                FROM pokemon_coords 
                WHERE created > to_timestamp($1) AND created <= to_timestamp($2)  -- Filter out old alerts
                  AND despawn > NOW() 
                  AND iv >= $3 AND iv <= $4
                  AND cp>= $5 AND cp<=$6
                  AND lvl>=$7 AND lvl<=$8
                """

                params = [last_checking_time,current_checking_time ,filter_minIv, filter_maxIv,filter_minCp,filter_maxCp,filter_minLvl,filter_maxLvl]
                if not filter_gender == "A":
                    query += " AND gender = $9"
                    params.append(filter_gender)
                if filter_mons and filter_mons[0] != 'all':
                    if filter_gender == "A":
                        query += " AND p_name = ANY($9::TEXT[])"  # Pokémon filter is $9 if gender is omitted
                        params.append(filter_mons)
                    else:
                        query += " AND p_name = ANY($10::TEXT[])"  # Pokémon filter is $10 if gender is included
                        params.append(filter_mons)
                query += ";"
                return await conn.fetch(query, *params)

        except Exception as e:
            print("Error fetching data from DB:", e)
            return []

# async def test():
#     async with PGDB() as pq:
#         print(datetime.datetime.now())
#         data=await pq.fetch_filtered_data(100,100,[],True,datetime.datetime.now())
#         print(data)
# asyncio.run(test())