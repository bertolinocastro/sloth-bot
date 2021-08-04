import discord
# from discord.ext import commands, menus, tasks
from discord.ext import commands, tasks
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
lesson_management_role_id = int(os.getenv('LESSON_MANAGEMENT_ROLE_ID'))
class_management_channel_id = int(os.getenv('CLASS_MANAGEMENT_CHANNEL_ID'))
class_management_approval_channel_id = int(os.getenv('CLASS_MANAGEMENT_APPROVAL_CHANNEL_ID'))
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
        self.msg_to_react_id = None

    @commands.Cog.listener()
    async def on_ready(self) -> None:

        self.guild = self.client.get_guild(server_id)
        self.class_mng_channel = self.client.get_channel(class_management_channel_id)
        self.class_mng_approval_channel = self.client.get_channel(class_management_approval_channel_id)

        # DNK: Check whether you want to simply use a msg_id for that msg or use it like this...
        await self.get_msg_to_react()

        self.client.add_view(ChannelLessonManagementView(self.client))

        view = View(timeout=None)
        view.add_item(CLMVConfirm(
            custom_id='approve_new_class_request_id',
            states=None,
            embed=None,
            client=self.client,
            langs=None,
            func=approve_new_class_request,
            style=discord.ButtonStyle.green,
            label='Approve',
            emoji='\U00002705'
        ))
        view.add_item(CLMVConfirm(
            custom_id='deny_new_class_request_id',
            states=None,
            embed=None,
            client=self.client,
            langs=None,
            func=deny_new_class_request,
            style=discord.ButtonStyle.red,
            label='Deny',
            emoji='\U0001F590'
        ))
        self.client.add_view(view)

        self.alert_forgetful_teachers.start()

        print('ClassManagement cog is ready!')

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_class_management_embed_view(self, ctx) -> None:
        ''' (ADM) Empties Class Management Channel and inserts embeds. '''

        if self.class_mng_channel != ctx.channel:
            return

        await self.class_mng_channel.purge()

        embed = self.lesson_mng_embed()

        view = ChannelLessonManagementView(self.client)

        msg = await self.class_mng_channel.send(embed=embed, view=view)


    def lesson_mng_embed(self) -> discord.Embed:
        embed = discord.Embed(title='Lesson Management Menu',
                              description='Welcome to the Lesson Management Menu. Here you have the options to add and remove your classes and also manage when you will do them!', color=discord.Colour.from_rgb(234,72,223))
        embed.add_field(name=':calendar_spiral: Calendar',
                        value='Open the [calendar](https://thelanguagesloth.com/class/calendar/) to see the classes!', inline=False)
        embed.add_field(name=':grey_question: FAQ',
                        value="1. **I can't see a language to select**\nSloth shows only the languages matching the ones in your roles\n2. **I can't see the time I want to teach**\nSloth shows only available hours based on the day and languages you chose, based on rules defined by the Lesson Management Team", inline=False)

        return embed



    async def get_msg_to_react(self):
        async for msg in self.class_mng_channel.history(oldest_first=True):
            if len(msg.embeds) and msg.author.id == bot_id and \
                self.lesson_mng_embed().to_dict() in [a.to_dict() for a in msg.embeds]:
                self.msg_to_react_id = msg.id

        # if self.msg_to_react_id is None:
        #     print('Couldn\'t find the bot message in the class management channel. Creating a new one.')
        #     await self.create_class_management_embed_view_task()
        # else:
        #     print('Found the class management embed!')


    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def missing_teacher_requests(self, ctx, clean: bool = False) -> None:
        ''' Recreate all embeds that are still in the database waiting to be approved.
        :param bool clean: Whether to purge entire channel '''

        if self.class_mng_approval_channel != ctx.channel:
            return

        if clean:
            # threads = await self.class_mng_approval_channel.active_threads()
            # threads_active_ids = []
            # for thread in threads:
            #     first_msg = (await (thread.history(limit=1)).flatten())[0]
            #     threads_active_ids.append(first_msg.id)
            #
            # pprint(threads_active_ids)
            # def has_no_active_thread(m):
            #     return m.id not in threads_active_ids
            #
            # await self.class_mng_approval_channel.purge(check=has_no_active_thread)

            await self.class_mng_approval_channel.purge()

        requests = await TeacherDB.get_all_class_requests()

        if not len(requests):
            await ctx.send("**There's no remaining Teacher request to be analysed!**\nAlthough there might be opened cases in active threads.", delete_after=15)

        for request in requests:

            member = self.guild.get_member(request['teacher_id'])

            extend_request_as_in_view(request)

            await send_request_in_approval_channel(request, member, self.client)

            # trying to prevent rate limit as this command might send too many messages in a row
            await asyncio.sleep(.5)






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

        if await TeacherDB.table_exists('PermanentClasses'):
            return await ctx.send("**Table `PermanentClasses` already exists!**")

        await TeacherDB.create_permanent_classes_table()
        await ctx.send("**Table __PermanentClasses__ created!**")


    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_permanent_classes_occurrences_table(self, ctx):
        '''Create the classes occurrences table in the database'''

        if await TeacherDB.table_exists('PermanentClassesOccurrences'):
            return await ctx.send("**Table `PermanentClassesOccurrences` already exists!**")

        await TeacherDB.create_permanent_classes_occurrences_table()
        await ctx.send("**Table __PermanentClassesOccurrences__ created!**")


    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_extra_classes_table(self, ctx):
        '''Create the classes table in the database'''

        if await TeacherDB.table_exists('ExtraClasses'):
            return await ctx.send("**Table `ExtraClasses` already exists!**")

        await TeacherDB.create_extra_classes_table()
        await ctx.send("**Table __ExtraClasses__ created!**")


    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_lesson_approval_requests_table(self, ctx):
        '''Create the LessonApprovalRequests table in the database'''

        if await TeacherDB.table_exists('LessonApprovalRequests'):
            return await ctx.send("**Table `LessonApprovalRequests` already exists!**")

        await TeacherDB.create_lesson_approval_requests_table()
        await ctx.send("**Table __LessonApprovalRequests__ created!**")


    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_lesson_approval_requests_table(self, ctx):
        '''Drop the LessonApprovalRequests table in the database'''

        if not await TeacherDB.table_exists('LessonApprovalRequests'):
            return await ctx.send("**Table `LessonApprovalRequests` doesn't exist!**")

        await TeacherDB.drop_table('LessonApprovalRequests')
        await ctx.send("**Table __LessonApprovalRequests__ dropped!**")


    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_permanent_classes_table(self, ctx):
        '''Drop the classes table in the database'''

        if not await TeacherDB.table_exists('PermanentClasses'):
            return await ctx.send("**Table `PermanentClasses` doesn't exist!**")

        await TeacherDB.drop_table('PermanentClasses')
        await ctx.send("**Table __PermanentClasses__ dropped!**")


    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_permanent_classes_occurences_table(self, ctx):
        '''Drop the classes table in the database'''

        if not await TeacherDB.table_exists('PermanentClassesOccurrences'):
            return await ctx.send("**Table `PermanentClassesOccurrences` doesn't exist!**")

        await TeacherDB.drop_table('PermanentClassesOccurrences')
        await ctx.send("**Table __PermanentClassesOccurrences__ dropped!**")


    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_extra_classes_table(self, ctx):
        '''Drop the classes table in the database'''

        if not await TeacherDB.table_exists('ExtraClasses'):
            return await ctx.send("**Table `ExtraClasses` doesn't exist!**")

        await TeacherDB.drop_table('ExtraClasses')
        await ctx.send("**Table __ExtraClasses__ dropped!**")


    # this command should be in another related Cog
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_languages_table(self, ctx):
        '''Create the languages table in the database'''

        if await TeacherDB.table_exists('Languages'):
            return await ctx.send("**Table `Languages` already exists!**")

        await TeacherDB.create_languages_table()
        await ctx.send("**Table __Languages__ created!**")


    # this command should be in another related Cog
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_languages_table(self, ctx):
        '''Create the languages table in the database'''

        if not await TeacherDB.table_exists('Languages'):
            return await ctx.send("**Table `Languages` doesn't exist!**")

        await TeacherDB.drop_table('Languages')
        await ctx.send("**Table __Languages__ dropped!**")


    # this command should be in another related Cog
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def insert_prelisted_languages_table(self, ctx):
        '''Create the languages table in the database'''

        if not await TeacherDB.table_exists('Languages'):
            return await ctx.send("**Table `Languages` doesn't exist!**")

        await TeacherDB.insert_prelisted_languages_table()
        await ctx.send("**Prelisted languages in __Languages__ inserted!**")


def setup(client):
    client.add_cog(ClassManagement(client))
