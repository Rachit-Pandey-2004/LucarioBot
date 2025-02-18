'''
we can implement geo data storage in future
'''

from configparser import ConfigParser
from os import getcwd
import redis.asyncio as redis
from redis import exceptions
import asyncio
from time import time

class Caching:
    def __init__(self):
        try:
            filename="%s/cache/config.ini" % getcwd()
            section="redis"
            parser = ConfigParser()
            parser.read(filename)
            redis_config = {}
            if parser.has_section(section):
                parms = parser.items(section)
                for items in parms:
                    redis_config[items[0]] = items[1]
            else:
                raise Exception("Section {0} not found in the {1} file".format(section, filename))
        
            self.caching=redis.Redis(host = redis_config['hostname'],port = redis_config['port_number'],password=redis_config['password'],decode_responses = True)
        except exceptions as e:
            print("error while stablishing caching pipelines\n-> ",e)
        else:
            print("caching pipeline dugged successfully ...")

    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.caching.aclose()
        pass
    async def insert_mon_coords(self,unique,coord,expiry:int)->bool:
        try:
            await self.caching.set(name=unique,value=coord,ex=expiry)
        except Exception as e:
            print("Error has occured while caching !! \n",e)
            return False
        else:
            return True
        
    async def fetch_mon_coords(self,unique)->str:
        value= await self.caching.get(name=unique)
        return value
    async def check_expired(self,unique)->bool:
        '''
        if data is expired then return true 
        else return false to denote that not expired
        '''
        ttl=await self.caching.ttl(name=unique)
        if ttl>=0:
            return False
        return True
    
async def test():
    async with Caching() as ch:
        state = await ch.insert_mon_coords("p1","26.00123, -120.457823",expiry=3)
        await asyncio.sleep(2)
        state=await ch.check_expired("p1")
        if not state:
            state = await ch.fetch_mon_coords("p1")
            print(state)
        else :
            print("expired . . . ")

if __name__=="__main__":
    asyncio.run(test())
