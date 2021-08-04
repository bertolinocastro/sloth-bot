import json
import asyncio
from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import UserCreds, ClientCreds
from pprint import pprint

# WARNING: The initial pipeline is not done here!
# ........ In order to get the token file, you have to execute
# ........ the google default pipeline!
# ........ It's possible to use solely the aiogoogle library,
# ........ but it's not implemented yet

with open('credentials_calendar.json') as f:
	creds = json.load(f)['installed'] # <---- Check whether this is the top-level key in your credentials.json file!

with open('token_calendar.json') as f:
	token = json.load(f)

user_creds = UserCreds(
	access_token=token['token'],
	refresh_token=token['refresh_token'],
	expires_at=token['expiry']
)

client_creds = ClientCreds(
	client_id=creds['client_id'],
	client_secret=creds['client_secret'],
	scopes=token['scopes']
)

def new_session(func):
	async def inner(*args, **kwargs):
		async with Aiogoogle(user_creds=user_creds, client_creds=client_creds) as aiog:
			gcal = await aiog.discover('calendar','v3')
			res = await func(aiog, gcal, *args, **kwargs)
		return res
	return inner

@new_session
async def get_calendar(aiog, gcal):

	pprint(gcal)
	return gcal, aiog

asyncio.run(get_calendar())
