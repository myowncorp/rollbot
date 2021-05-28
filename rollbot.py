#discord
import discord
from discord.ext import commands, tasks

#google
from google.oauth2 import service_account
from googleapiclient.discovery import build
import googleapiclient

#standard
import random
import os
import asyncio
from datetime import datetime, time, timedelta

# google sheets
SERVICE_ACC_FILE='keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']
SPREADSHEET_ID = os.getenv('FUNBOT_SHEET')
RANGE_NAME = 'daily!daily_rolls'
creds = None
creds = service_account.Credentials.from_service_account_file(SERVICE_ACC_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

# this is the sheet
sheet = service.spreadsheets()

# discord 
THE_KEY = os.getenv('FUNBOT_KEY')
localtime = datetime.now() # on heroku this is going to be set as GMT
resettime = time(hour=3, second=0, minute=0,)
resettime = datetime.combine(localtime.date(), resettime)

bot = commands.Bot(command_prefix='$')



def timeUntilResetInMin(tm, rt):
	
	
	''' returns the time until the server resets at 2300 in minutes ETC
		tm - time                is a  datetime.datetime
		rt - reset time          is a  datetime.datetime
		returns delta.seconds/60 is an integer[1-1439]'''

	if tm.hour >= rt.hour:
		rt = rt.replace(day=tm.day+1)
		delta = rt - tm
		print(delta)
	#tm.hour < rt.hour	
	else:
		delta = rt-tm
		print(delta)
	return ((delta.seconds/60))
		

	

@commands.cooldown(1, 15, commands.BucketType.user)
@bot.command()
async def roll(ctx):
	
	''' Roll the die '''
	# get a random number
	r = random.randrange(1, 100, 1)
	# send the roll
	await ctx.send(f'Your roll **{ctx.message.author.name}**: {r}')
	# initialize daily as True
	daily = True
	# return a dictionary with {"majorDimension", "values", and some else}
	resp = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
	# This will be a list of lists
	vals = resp['values']
	
	# iterate over the rows
	for row in vals:
		# index 0 is always to be 'user'
		if row[0] == ctx.message.author.name:
			# if daily is ever false its always false
			daily = False
			return
		else:
			# it must be True everytime 
			daily = True
			
	# if the user has not rolled today we append it to the sheet
	if daily == True:           
		await ctx.send('this was ur first roll of the day')
		# put the values into a list of lists
		our_vals = [[ctx.message.author.name, str(r)]]
		# the body contains other kwargs so values needs to be specified
		our_body = {"values": our_vals}
		
		req = sheet.values().append(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
						body=our_body, valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS")
		resp = req.execute()
	



@commands.cooldown(1, 12, commands.BucketType.user)
@bot.command()
async def daily(ctx):
	
	# ''' will tell you your daily roll, if you have one.'''
	
	# init
	daily = 0
	# return a dictionary with {"majorDimension", "values", and some else}
	resp = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
	# This will be a list of lists
	vals = resp['values']
	for row in vals:
		# index 0 is always to be 'user'
		if row[0] == ctx.message.author.name:
			await ctx.message.channel.send('here is your roll: ' + row[0] + " : " + row[1])
			daily = False
			return
		else:
			daily = True
	if daily == True:
		await ctx.message.channel.send("no creo q you rolled today")


@commands.cooldown(1, 10, commands.BucketType.user)
@bot.command()
async def top(ctx):
	
	''' shows todays leaderboard '''
	resp = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="daily!A2:B20").execute()
	vals = resp['values']
	
	top = sorted(vals, key = lambda i: i[1])
	i = len(top)
	for row in top:
		await ctx.send(f"# {i} {row[0]} {row[1]} \n")
		i = i - 1

# @bot.command()
# @commands.check(check_is_tester1)
# async def addroll(ctx, name: str, roll: int):
	
	# ''' adds a roll to the daily leaderboard '''
	
	# with open('today.csv', 'a', newline='') as csvf:
		# fieldnames = ['user', 'today']
		# writer = csv.DictWriter(csvf, fieldnames=fieldnames)
		# writer.writerow({'user': f'{name}', 'today': f'{roll}'})
	# await ctx.send("Sucessfully updated the leaderboard")


@tasks.loop(hours=24.0)
async def maint():
	
	'''opens the file deletes everything and adds a header'''
	
	def the_delete():
		sheet.values().clear(spreadsheetId=SPREADSHEET_ID,range=RANGE_NAME).execute()
	
	print("maint loop has turned on...")
	print(f"is sleeping until:  + {timeUntilResetInMin(localtime, resettime)}")
	
	await asyncio.sleep(timeUntilResetInMin(localtime, resettime))
	the_delete()
	
	
# @bot.command()
# @commands.cooldown(1, 30, commands.BucketType.user)
# #@commands.check(check_is_tester1)
# async def wipedaily(ctx):

	# ''' wipes the daily leaderboard  '''
	# sheet.values().clear(spreadsheetId=SPREADSHEET_ID,range=RANGE_NAME).execute()
		
@bot.event
async def on_connect():
	print("just connected")
	print(f"the time is: {datetime.now()}")
	
	maint.start()
	
	
@bot.event
async def on_command_error(ctx, error):
	await ctx.send(error)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def resetwhen(ctx):
	
	''' tells you how much time in minutes until reset'''
	
	await ctx.send(timeUntilResetInMin(datetime.now(), resettime))
	


@bot.event
async def on_disconnect():
	print("bot going offline")
		
#the key
bot.run(THE_KEY)
