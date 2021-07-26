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
            print('entrou no emoji')

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
        print('entrei no teacher request!')

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

        pprint(dm_ctx.__dict__)
        pprint(dm_ctx.author)
        res = await ClassManagementMenuTeacher(dm_ctx, zeroth_msg, member).begin()

    @commands.command(hidden=True)
    async def teste_bagunca(self, ctx) -> None:
        ''' (ADM) Empties Class Management Channel and inserts embeds. '''

        pprint(ctx.__dict__)
        pprint(ctx.author)
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


class ClassManagementMenuTeacher(menus.Menu):
    ''' Class related to Class Management actions done by teachers '''

    # adicao
    # remocao
    # pausa
    # alteracao de horario

    reaction_check = dm_reaction_check

    def __init__(self, ctx: discord.ext.commands.Context, msg: discord.Message, member: discord.Member):
    # def __init__(self, msg: discord.Message, member: discord.Member):
        super().__init__(timeout=60,delete_message_after=False,clear_reactions_after=True)
        self.member = member
        # self.content = content
        self.msg = msg
        self.ctx = ctx
        self.result = None
        self.changes = {}
        self.current_classes = {}


    async def begin(self):
        await self.start(self.ctx, wait=True)
        # await self.start(self.ctx)
        return self.result


    async def send_initial_message(self, ctx, channel):

        embed = discord.Embed(
            title="**You called me in the class management channel.**",
            description="What do you want to do?\n\nYour current schedule is:",
            color=discord.Colour.from_rgb(234,72,223)
        )
        await self.teacher_classes_overview_embed(embed)

        self.button_descriptions_embed(embed)

        # self.msg = await channel.send(embed=embed)
        # self.msg2 = await channel.send(embed=embed)
        await self.msg.edit(content=None, embed=embed)

        return self.msg


    async def teacher_classes_overview_embed(self, embed):

        classes = await TeacherDB.get_teacher_classes(self.member.id)
        self.current_classes = classes
        pprint(classes)

        if classes is None:
            embed.add_field(
                name=':calendar_spiral: You have no classes registered!',
                value='Please ask lesson management to work with it out',
                inline=False
            )
            return embed

        embed.add_field(
            name=':calendar_spiral: Permament classes',
            value=classes['permanent'],
            inline=False
        )
        embed.add_field(
            name=':calendar_spiral: Extra classes',
            value=classes['extra'],
            inline=False
        )

        return embed


    def button_descriptions_embed(self, embed):
        embed.set_footer(
            text='\U0001F4E5 add a class\t\U0001F4E4 remove a class\n\U0001F4C5 edit a class\t\U000023F0 pause classes'
        )
        return embed


    async def finalize(self, timeout):

        embed = discord.Embed(
            title="**Thank you for teaching!**",
            description="Your requests, if any, were sent to the Lesson Management Team!\n\nYour latest schedule is:",
            color=discord.Colour.from_rgb(234,72,223)
        )
        await self.teacher_classes_overview_embed(embed)

        await self.changes_done(embed)
        # self.button_descriptions_embed(embed)

        # self.msg = await channel.send(embed=embed)
        await self.msg.edit(content=None, embed=embed)


    async def changes_done(self, embed):
        yes   = ":white_check_mark:"
        no    = ":x:"
        maybe = ":hourglass:"
        yesno   = [no, yes]
        maybeno = [no, maybe]

        changes_str = '\n'.join(
            [f'[{maybeno[x.status]}]: {x}' for x in self.changes['add']]+
            [f'[{maybeno[x.status]}]: {x}' for x in self.changes['edit']]+
            [f'[{yesno[x.status]}]: {x}' for x in self.changes['removal']]+
            [f'[{yesno[x.status]}]: {x}' for x in self.changes['pause']]
        )

        embed.add_field(
            name=':notebook_with_decorative_cover: Changes',
            values=changes_str,
            inline=False
        )

        pass


    # adicao - needs approval
    @menus.button('\U0001F4E5')
    async def do_add(self, payload):
        print('Entrei  no do addd')
        # self.show_available_slots(payload)
        languages = await TeacherDB.get_taught_languages()
        pprint(languages)
        print('Entrei no button do add')

        try:
            self.changes['add'] = await ClassManagementMenuTeacherAdd(self.ctx, self.msg, self.member, self.current_classes, languages).begin()
        except Exception as e:
            print('Na hora de criar o menuteacheradd, da esse erro aqui: ',e)
            PrintException()
        print('recebi resposta do ClassManagementMenuAdd')
        pass

    # alteracao de horario - needs approval
    @menus.button('\U0001F4C5')
    async def do_edit(self, payload):
        pass

    # remocao - no approval
    @menus.button('\U0001F4E4')
    async def do_remove(self, payload):
        pass

    # pausa - no approval
    @menus.button('\U000023F0')
    async def do_pause(self, payload):
        pprint(payload)
        pass

    # finalise
    @menus.button('\U0001F44B')
    async def do_stop(self, payload):
        pprint(payload)
        # print(payload.member)
        # await self.msg.edit(content=None)
        self.stop()

        pass




def setup(client):
    client.add_cog(ClassManagement(client))
