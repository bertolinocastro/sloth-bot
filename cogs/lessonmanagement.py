import discord
from discord.ext import commands, menus, tasks
from mysqldb import *
from extra.lessonmanagementmenus import *
from extra.teacherDB import TeacherDB
import asyncio
import os
# from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from extra.calendarapi import *
from pprint import pprint

from extra.menu import ConfirmSkill

server_id = int(os.getenv('SERVER_ID'))
teacher_role_id = int(os.getenv('TEACHER_ROLE_ID'))
class_management_channel_id = int(os.getenv('CLASS_MANAGEMENT_CHANNEL_ID'))
report_channel_id = int(os.getenv('REPORT_CHANNEL_ID'))
bot_id = int(os.getenv('BOT_ID'))


# TODO: convert googleapi usage into asynchronous mode
# ..... https://aiogoogle.readthedocs.io/en/latest/

# connecting to google calendar & spreasheets API
# gscopes = ['https://www.googleapis.com/auth/spreadsheets']
# gspreadsheet_id = os.getenv('GOOGLE_SPREEDSHEET_ID')
# creds = None
# if os.path.exists('token_calendar.json'):
#     creds = Credentials.from_authorized_user_file('token_calendar.json', gscopes)
# if not creds or not creds.valid:
#     if creds and creds.expired and creds.refresh_token:
#         creds.refresh(Request())
#     else:
#         flow = InstalledAppFlow.from_client_secrets_file(
#             'credentials_slothsheet.json', gscopes)
#         creds = flow.run_local_server(port=0)
#     with open('token_calendar.json', 'w') as token:
#         token.write(creds.to_json())
# gservice = build('sheets', 'v4', credentials=creds)
# gsheets = gservice.spreadsheets()
# calendar = Calendar(gsheets, gspreadsheet_id) # object defined in calendarapi.py
# end of g API


class ClassManagement(commands.Cog):
    '''
    A cog related to the management of classes in the server.
    '''

    # ver classes permanentes e classes extras com base na tabela!

    def __init__(self, client) -> None:

        self.client = client
        self.classmanagement_emoji = '✍️'
        self.msg_to_react_id = None

    @commands.Cog.listener()
    async def on_ready(self) -> None:

        self.class_mng_channel = self.client.get_channel(class_management_channel_id)

        # DNK: Check whether you want to simply use a msg_id for that msg or use it like this...
        await self.get_msg_to_react()

        self.alert_forgetful_teachers.start()

        print('ClassManagement cog is ready!')


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload) -> None:
        ''' Handles Class Management related . '''

        if not payload.guild_id or not payload.member or \
            payload.member.bot or \
            payload.channel_id != class_management_channel_id or \
            payload.message_id != self.msg_to_react_id:
            return

        # starts to chat with teacher to manage the classes stuff
        if payload.emoji.name == self.classmanagement_emoji:
            # print('entrou no emoji')

            await self.handle_teacher_request(payload)
        # elif :
        #
        # else:


        # m = MyMenu()
        # await m.start(ctx)


        pass


    def lesson_mng_embed(self) -> discord.Embed:
        embed = discord.Embed(title='Lesson Management Menu',
                              description='Welcome to the Lesson Management Menu. Here you have the options to add and remove your classes and also manage when you will do them!', color=discord.Colour.from_rgb(234,72,223))
        embed.add_field(name=':calendar_spiral: Calendar',
                        value='Open the [calendar](https://thelanguagesloth.com/class/calendar/) to see the classes!', inline=False)
        embed.add_field(name='React below with:',
                        value=self.classmanagement_emoji+' if you want to start to chat directly with me to manage your classes!', inline=False)

        return embed


    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_class_management_embed(self, ctx) -> None:
        ''' (ADM) Empties Class Management Channel and inserts embeds. '''

        if self.class_mng_channel != ctx.channel:
            return

        await create_class_management_embed_task()


    async def create_class_management_embed_task(self) -> None:

        await self.class_mng_channel.purge()

        embed = self.lesson_mng_embed()

        msg = await self.class_mng_channel.send(embed=embed)

        self.msg_to_react_id = msg.id

        await msg.add_reaction(self.classmanagement_emoji)


    async def handle_teacher_request(self, payload) -> None:
        # print('entrei no teacher request!')

        member = payload.member

        if member.guild.id != server_id:
            await member.send(embed=discord.Embed(
                title='You\'re not allowed to do it!',
                description='In order to do that, you have first to become a member of [The Language Sloth Server](https://discord.gg/Dr9EkQph)!',
                color=discord.Colour.from_rgb(0,0,0)
            ))
            return

        if teacher_role_id not in [x.id for x in member.roles]:
            await member.send(embed=discord.Embed(
                title='You\'re not allowed to do that!',
                description='In order to do that, you have to be a Teacher.',
                color=discord.Colour.from_rgb(0,0,0)
            ).add_field(
                name='Apply to become a Teacher',
                value=f'Apply in the channel <#{report_channel_id}>'
            ))
            return

        # from now on create sequence of "menus.Menu" interactions here
        # so the teachers can work with the management pipelines

        # zeroth_msg = await member.send('Starting class management...')
        zeroth_msg = await member.send('Starting class management...')
        dm_ctx = await self.client.get_context(zeroth_msg)

        # pprint(dm_ctx.__dict__)
        # pprint(dm_ctx.author)
        try:
            res = await ClassManagementMenuTeacher(dm_ctx, zeroth_msg, member).begin()
        except:
            PrintException()

    @commands.command(hidden=True)
    async def teste_bagunca(self, ctx) -> None:
        ''' (ADM) Empties Class Management Channel and inserts embeds. '''

        # pprint(ctx.__dict__)
        # pprint(ctx.author)
        confirm = await ConfirmSkill('nada não').prompt(ctx)



    async def get_msg_to_react(self):
        async for msg in self.class_mng_channel.history(oldest_first=True):
            if len(msg.embeds) and msg.author.id == bot_id and \
                self.lesson_mng_embed().to_dict() in [a.to_dict() for a in msg.embeds]:
                self.msg_to_react_id = msg.id

        if self.msg_to_react_id is None:
            print('Couldn\'t find the bot message in the class management channel. Creating a new one.')
            await self.create_class_management_embed_task()
        else:
            print('Found the class management embed!')





    # TODO: make this coroutine work in specific "minutes of hours"
    # ..... smthing like "always at 1:15, 2:15, 3:15, etc"
    @tasks.loop(minutes=60)
    async def alert_forgetful_teachers(self):
        # calendar.ge
        print('allerting forgetful teachers')

        pass


    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_permanent_classes_table(self, ctx):
        '''Create the classes table in the database'''

        if await self.table_exists('PermanentClasses'):
            return await ctx.send("**Table `PermanentClasses` already exists!**")

        # class id (primary key), teacher id, teacher name, class language, class day, class time, is still active
        # day_of_week 0 = sunday ... 6 = saturday
        # time 0 = midnight ... 23 = 11 PM

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE PermanentClasses (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                teacher_id BIGINT NOT NULL,
                teacher_name VARCHAR(100) NOT NULL,
                language VARCHAR(50) NOT NULL,
                day_of_week ENUM('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'),
                time TINYINT UNSIGNED NOT NULL,
                is_active BOOL NOT NULL,
                date_of_creation DATE NOT NULL DEFAULT NOW(),
                date_of_inactivation DATE)""")
                # day_of_week TINYINT UNSIGNED NOT NULL,
        await db.commit()
        await mycursor.close()


    @commands.command
    @commands.has_permissions(administrator=True)
    async def create_permanent_classes_occurrences_table(self, ctx):
        '''Create the classes occurrences table in the database'''

        if await self.table_exists('PermanentClassesOccurrences'):
            return

        # class id (primary key), date of occurrence, type of occurence, details
        # Types: hosted (green), not hosted (red), cancelled on the day itself (orange), cancelled previously 1 or more classes [paused] (purple)

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE PermanentClassesOccurrences (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                permanent_class_id BIGINT NOT NULL,
                date DATE NOT NULL,
                type ENUM('Hosted','Missed','Cancelled','Paused')
                details VARCHAR(150),
                FOREIGN KEY (permanent_class_id) REFERENCES PermanentClasses(id)
            )
            """)
                # type TINYINT NOT NULL,
        await db.commit()
        await mycursor.close()


    # async def insert_new_permanent_class(self)
        # pass


    async def table_exists(self, table: str):
        table_info = await self.fetchall_db(
            f"SHOW TABLE STATUS LIKE '{table}'"
        )
        return len(table_info) != 0


    async def fetchall_db(self, query : str):
        mycursor, db = await the_database()
        await mycursor.execute(query)
        table_info = await mycursor.fetchall()
        await mycursor.close()
        return table_info



def setup(client):
    client.add_cog(ClassManagement(client))
