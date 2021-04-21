import redis
import pdb
conn = redis.Redis('localhost')

# user = {"Name":"Pradeep", "Company":"SCTL", "Address":"Mumbai", "Location":"RCP"}

# conn.hmset("pythonDict", user)

print(conn.hgetall("pythonDict"))
pdb.set_trace()

uni_time_triggers = redisdb.hgetall("uni_time_triggers")
redisdb.hmset("uni_time_triggers", uni_time_triggers)