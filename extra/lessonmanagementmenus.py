import discord
from discord.ext import commands, menus, tasks
from discord.ui import View, Button, Select
from discord.ext import commands, tasks
from extra.teacherDB import TeacherDB

from mysqldb import *
import asyncio

from datetime import date, timedelta

import linecache
import sys
import os
from pprint import pprint

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


class_management_channel_id = int(os.getenv('CLASS_MANAGEMENT_CHANNEL_ID'))
class_management_approval_channel_id = int(os.getenv('CLASS_MANAGEMENT_APPROVAL_CHANNEL_ID'))
# teacher_role_id = int(os.getenv('TEACHER_ROLE_ID'))
# report_channel_id = int(os.getenv('REPORT_CHANNEL_ID'))
lesson_management_role_id = int(os.getenv('LESSON_MANAGEMENT_ROLE_ID'))
owner_role_id = int(os.getenv('OWNER_ROLE_ID'))
admin_role_id = int(os.getenv('ADMIN_ROLE_ID'))
# approval_authorized_roles = [lesson_management_role_id, admin_role_id, owner_role_id]
approval_authorized_roles = [lesson_management_role_id] # Muffin que se vire pra pegar a role de lesson management se ela não tiver kakaka


class ChannelLessonManagementView(View):

    def __init__(self, client):
        super().__init__(timeout=None)
        self.client = client
        pass


    async def teacher_classes_overview_embed(self, member):

        classes = await TeacherDB.get_teacher_classes(member.id)

        embed = discord.Embed(
            title="**Your current schedule is:**",
            description="",
            color=discord.Colour.from_rgb(234,72,223)
        )

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


    @discord.ui.button(
        style=discord.ButtonStyle.green,
        label='New class',
        disabled=False,
        custom_id='clmv_new_class',
        emoji='\U0001F4E5',
        row=0
    )
    async def new_class(self, btn: Button, interaction: discord.Interaction):
        ''' Handles Class Management related . '''

        if not interaction.guild_id or not interaction.user or \
            interaction.user.bot:
            return

        member = interaction.user

        embed = await self.teacher_classes_overview_embed(member)
        languages = await TeacherDB.get_taught_languages()

        states = {}
        # view = AddLessonView(states, embed, self.client, ['pt','en','de'])
        view = AddLessonView(states, embed, self.client, languages)


        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)



    @discord.ui.button(
        style=discord.ButtonStyle.green,
        label='Edit a class',
        disabled=False,
        custom_id='clmv_edit_class',
        emoji='\U0001F4C5',
        row=0
    )
    async def edit_class(self, btn: Button, interaction: discord.Interaction):
        ''' Handles Class Management related . '''

        if not interaction.guild_id or not interaction.user or \
            interaction.user.bot:
            return

        member = interaction.user


        await interaction.response.send_message('edit', ephemeral=True)


    @discord.ui.button(
        style=discord.ButtonStyle.green,
        label='Delete a class',
        disabled=False,
        custom_id='clmv_del_class',
        emoji='\U0001F4E4',
        row=0
    )
    async def del_class(self, btn: Button, interaction: discord.Interaction):
        ''' Handles Class Management related . '''

        if not interaction.guild_id or not interaction.user or \
            interaction.user.bot:
            return


        member = interaction.user


        await interaction.response.send_message('del', ephemeral=True)


    @discord.ui.button(
        style=discord.ButtonStyle.green,
        label='Pause/Cancel a class',
        disabled=False,
        custom_id='clmv_cancel_class',
        emoji='\U000023F0',
        row=0
    )
    async def cancel_class(self, btn: Button, interaction: discord.Interaction):
        ''' Handles Class Management related . '''

        if not interaction.guild_id or not interaction.user or \
            interaction.user.bot:
            return


        # member = payload.member
        member = interaction.user


        await interaction.response.send_message('cancel', ephemeral=True)



class AddLessonView(View):

    def add_disabled_btn(self, label, row=None, color=discord.ButtonStyle.blurple):
        self.add_item(Button(
            disabled=True,
            style=color,
            label=label,
            row=row
        ))


    def __init__(self, states, embed, client, langs=None):
        super().__init__(timeout=120)

        if 'selected_lang' not in states:
            async def set_selected_lang(self):
                self.states['selected_lang'] = self.values[0]

            for i in range(0, len(langs), 25):
                self.add_item(
                    # LangsSelect(
                    ClassManagementSelect(
                        states,
                        embed,
                        langs,
                        func=set_selected_lang,
                        client=client,
                        placeholder='Select a language',
                        # custom_id=f'clmv_sel_lang_{i}',
                        options=[
                            discord.SelectOption(
                                label=label
                            )
                            for label in langs[i:i+25]
                        ]
                    )
                )
            return
        else:
            self.add_disabled_btn(f"Teaching {states['selected_lang']}")

        if 'selected_used_lang' not in states:
            async def set_selected_lang(self):
                self.states['selected_used_lang'] = self.values[0]

            for i in range(0, len(langs), 25):
                self.add_item(
                    # LangsSelect(
                    ClassManagementSelect(
                        states,
                        embed,
                        langs,
                        func=set_selected_lang,
                        client=client,
                        placeholder='Select the language you will speak',
                        # custom_id=f'clmv_sel_used_lang_{i}',
                        options=[
                            discord.SelectOption(
                                label=label
                            )
                            for label in langs[i:i+25]
                        ]
                    )
                )
            return
        else:
            self.add_disabled_btn(f"in {states['selected_used_lang']}")

        if 'is_permanent' not in states:

            async def set_is_permanent(self):
                self.states['is_permanent'] = self.values[0] == 'True'

            self.add_item(
                ClassManagementSelect(
                    states,
                    embed,
                    langs,
                    func=set_is_permanent,
                    client=client,
                    placeholder='Is it a permanent class?',
                    row=1,
                    options=[
                        discord.SelectOption(
                            label=label,
                            value=value
                        )
                        for label, value in [['Yes', True], ['No', False]]
                    ]
                )
            )
            return
        else:
            is_permanent = states['is_permanent']
            self.add_disabled_btn(f"{['as extra','permanently'][is_permanent]}")

        # TODO: add select to get month + date (listing the next 30 days)
        # ..... when it is an extra class
        if 'week_day' not in states and 'date_to_occur' not in states:
            if states['is_permanent']:
                async def set_week_day(self):
                    self.states['date_to_occur'] = None
                    self.states['week_day'] = self.values[0]
                    times = await TeacherDB.get_available_hours(**self.states)
                    self.states['times'] = times

                self.add_item(
                    ClassManagementSelect(
                        states,
                        embed,
                        langs,
                        func=set_week_day,
                        client=client,
                        placeholder='Select a week day',
                        row=1,
                        options=[
                            discord.SelectOption(
                                label=label
                            )
                            for label in ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
                        ]
                    )
                )
            else:
                async def set_date_to_occur(self):
                    d = date.fromisoformat(self.values[0])
                    self.states['date_to_occur'] = self.values[0]
                    self.states['date_to_occur_pretty'] = d.strftime("%d of %B")
                    self.states['week_day'] = d.strftime("%A")
                    times = await TeacherDB.get_available_hours(**self.states)
                    self.states['times'] = times

                self.add_item(
                    ClassManagementSelect(
                        states,
                        embed,
                        langs,
                        func=set_date_to_occur,
                        client=client,
                        placeholder='Select a date',
                        row=1,
                        # max_values=21,
                        options=[
                            discord.SelectOption(
                                label=value.strftime("%d of %B"),
                                value=value.isoformat()
                            )
                            for value in get_future_dates()
                        ]
                    )
                )
            return
        else:
            if states['is_permanent']:
                self.add_disabled_btn(f"on {states['week_day']}s")
            else:
                self.add_disabled_btn(f"on {states['date_to_occur_pretty']}")

        if 'time' not in states:
            async def set_time(self):
                self.states['time'] = self.values[0]

            self.add_item(
                ClassManagementSelect(
                    states,
                    embed,
                    langs,
                    func=set_time,
                    client=client,
                    placeholder='Select an available time',
                    row=1,
                    options=[
                        discord.SelectOption(
                            label=str(value)+' h',
                            value=value
                        )
                        for value in states['times']
                    ]
                )
            )
            return
        else:
            time = states['time']
            self.add_disabled_btn(f"at {time} h")


        if 'ok' not in states:
            self.add_item(CLMVConfirm(
                states,
                embed,
                client=client,
                langs=langs,
                func=send_new_class_request,
                style=discord.ButtonStyle.green,
                label='Send Request',
                emoji='\U00002705',
                row=1
            ))
            self.add_item(CLMVConfirm(
                states,
                embed,
                client=client,
                langs=langs,
                func=cancel_new_class_request,
                style=discord.ButtonStyle.red,
                label='JUST DON\'T',
                emoji='\U0001F590',
                row=1
            ))
        else:
            if states['ok']:
                self.add_disabled_btn(f"Finished!", color=discord.ButtonStyle.green, row=1)
            else:
                self.add_disabled_btn(f"Not sent!\n{states['not_ok_feedback']}", color=discord.ButtonStyle.red, row=1)


class ClassManagementSelect(Select):
    def __init__(self, states, embed, langs, client, func, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.states = states
        self.embed = embed
        self.langs = langs
        self.func = func
        self.client = client

    async def callback(self, interaction: discord.Interaction):
        await self.func(self)

        await interaction.response.edit_message(
            embed=self.embed,
            view=AddLessonView(
                self.states,
                self.embed,
                self.client,
                self.langs
            )
        )


class CLMVConfirm(Button):

    def __init__(self, states, embed, client, langs, func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.states = states
        self.embed = embed
        self.langs = langs
        self.func = func
        self.client = client

    async def callback(self, interaction: discord.Interaction):
        await self.func(self, interaction)


async def send_new_class_request(self, interaction: discord.Interaction):
    member = interaction.user

    states = self.states
    is_permanent = states['is_permanent']

    # has_similar = await TeacherDB.get_similar_lesson_approval_request(member.id, states['selected_lang'], states['selected_used_lang'], states['week_day'], states['time'], is_permanent)

    # setting 0 as message_id because the message was not sent yet
    # if you send the message into thhe approval channel, you can use here
    # the message id. This will prevent from using the lastrowid property
    # within the embed without having to send+edit the discord message
    lastrowid = await TeacherDB.insert_lesson_approval_request(member.id, member.name, states['selected_lang'], states['selected_used_lang'], states['week_day'], states['time'], is_permanent, 0, states['date_to_occur'])

    if lastrowid is None:
        self.states['ok'] = False
        self.states['not_ok_feedback'] = "There's still a similar recent request you sent under review!"

        await interaction.response.edit_message(
            embed=self.embed,
            view=AddLessonView(
                self.states,
                self.embed,
                self.client,
                langs=self.langs
            )
        )
        return

    self.states['ok'] = True

    await interaction.response.edit_message(
        embed=self.embed,
        view=AddLessonView(
            self.states,
            self.embed,
            self.client,
            langs=self.langs
        )
    )


    # await TeacherDB.insert_lesson_approval_request(member.id, member.name, states['selected_lang'], states['selected_used_lang'], states['week_day'], states['time'], is_active)

    if is_permanent:
        color=discord.Colour.from_rgb(234,72,223)
    else:
        color=discord.Colour.from_rgb(45,160,226)


    langroles = [x.name for x in member.roles if x.name.startswith('Native') or x.name.startswith('Fluent')]
    langroles_str = '**'+'**,**'.join(langroles)+'**' if len(langroles) else ''

    nick = "**"+member.nick+"**" if member.nick else ''

    # embed = discord.Embed(title=f'{member.name}',
                          # description=f"Requested for adding {['an Extra','a Permanent'][states['is_permanent']]} class:", color=color
    embed = discord.Embed(
        title=f"Request #{lastrowid}:\t\t\t\t\t\tAdd {['Extra','Permanent'][is_permanent]} class",
        # description=f"Check the [TLS Tracker](https://thelanguagesloth.com/tracker) for any inconsistences the bot couldn't get\n\n<@{member.id}> wants to add a new class",
        description=f"<@{member.id}> wants to add a new class",
        color=color)

    if is_permanent:
        embed.add_field(name='Class Info:',value=f"They want to teach **{states['selected_lang']}** using **{states['selected_used_lang']}**\n at **{states['time']}:00** __every__ **{states['week_day']}**", inline=False)
    else:
        embed.add_field(name='Class Info:',value=f"They want to teach **{states['selected_lang']}** using **{states['selected_used_lang']}**\n at **{states['time']}:00** __on__ **{states['date_to_occur_pretty']}, {states['week_day']}**", inline=False)


    embed.add_field(name='Teacher Info',value=f"Server nick: {nick}\nAccount nick: **{member.name}**\nRoles: {langroles_str}", inline=False)

    embed.set_footer(text="Check the TLS Tracker for any inconsistences the bot couldn't get")

    # embed.add_field(name='language_used',value=states['selected_used_lang'])
    # embed.add_field(name='day',value=states['week_day'])
    # embed.add_field(name='time',value=states['time'])
    # embed.add_field(name='permanent',value=is_permanent)
    embed.set_thumbnail(url=member.avatar.url)
    # embed.set_author(name=f"{member.nick or member.name}")
    embed.set_author(name='Link to TLS Tracker', url=f"https://thelanguagesloth.com/tracker", icon_url='https://thelanguagesloth.com/static/assets/images/favicon.png')


    view = View(timeout=None)
    view.add_item(CLMVConfirm(
        custom_id='approve_new_class_request_id',
        states=states,
        embed=embed,
        client=self.client,
        langs=self.langs,
        func=approve_new_class_request,
        style=discord.ButtonStyle.green,
        label='Approve',
        emoji='\U00002705'
    ))
    view.add_item(CLMVConfirm(
        custom_id='deny_new_class_request_id',
        states=states,
        embed=embed,
        client=self.client,
        langs=self.langs,
        func=deny_new_class_request,
        style=discord.ButtonStyle.red,
        label='Deny',
        emoji='\U0001F590'
    ))

    app_channel = self.client.get_channel(class_management_approval_channel_id)
    msg = await app_channel.send(embed=embed, view=view)

    await TeacherDB.update_msg_id_lesson_approval_request(lastrowid, msg.id)



async def cancel_new_class_request(self, interaction: discord.Interaction):
    self.states['ok'] = False

    await interaction.response.edit_message(
        embed=self.embed,
        view=AddLessonView(
            self.states,
            self.embed,
            self.client,
            langs=self.langs
        )
    )


async def approve_new_class_request(self, interaction: discord.Interaction):
    member = interaction.user


    # TODO: use the list approval_authorized_roles
    if not member.get_role(lesson_management_role_id):
        await interaction.response.send_message("**You don't have the right roles for this!**", ephemeral=True)
        return

    msg = interaction.message

    # embed = msg.embeds[0].to_dict()
    # fields = {}
    # for field in embed['fields']:
    #     fields[field['name']]=field['value']
    # pprint(fields)

    inserted = False
    # NOTE: all fields in `fields` have strings as values
    # if fields['permanent'] == 'True':
    #     pass
    #     # inserted = await TeacherDB.approve_permanent_class_request(msg.id)
    #     # inserted = await TeacherDB.insert_permanent_class(
    #     #     fields['id'], fields['name'], fields['language'], fields['language_used'], fields['day'], fields['time'], True
    #     # )
    # else:
    #     # await TeacherDB.insert_extra_class(
    #     #     fields['id'], fields['name'], fields['language'], fields['language_used'], fields['day'], fields['time'], True
    #     # )
    #     pass
    inserted = await TeacherDB.approve_permanent_class_request(msg.id)


    view = View(timeout=None)
    view.add_item(Button(
        disabled=True,
        style=discord.ButtonStyle.blurple if inserted else discord.ButtonStyle.gray,
        label=f'Approved by {member.name}' if inserted else 'Class already exists!',
        emoji='\U0001F512'
    ))

    await interaction.response.edit_message(
        embed=msg.embeds[0],
        view=view
    )


    # TODO: have a look in the info sent inside "embed". Maybe it would be better to reduce the amount of information  there
    await member.send('**We are happy to tell you that your request was approved!\nYou can look it in the [TLS calendar](https://thelanguagesloth.com/class/calendar/)**',embed=msg.embeds[0])


async def deny_new_class_request(self, interaction: discord.Interaction):
    member = interaction.user
    print('gostei desse babaca nao')
    msg = interaction.message
    view = View(timeout=None)
    view.add_item(Button(
        disabled=True,
        style=discord.ButtonStyle.red,
        label=f'Denied by {member.name}',
        emoji='\U0001F512'
    ))

    await interaction.response.edit_message(
        embed=msg.embeds[0],
        view=view
    )

    await TeacherDB.deny_class_request(msg.id)

    # TODO: have a look in the info sent inside "embed". Maybe it would be better to reduce the amount of information  there
    await member.send('**We are sorry to inform you that your request was denied.\nPlease review your request and check the [TLS calendar](https://thelanguagesloth.com/class/calendar/) to solve probable conflicting class hours. Remember: all classes are in CET time zone. If you have any questions, please, contact the Lesson Management Team #here (= some channel)**',embed=msg.embeds[0])


# TODO: this function below should only send a message
# ..... in teacher's DM to let they know whether the
# ..... Request was approved or denied
async def feedback_teacher_request(member, txt):

    pass



def get_future_dates():

    today = date.today()
    dt = timedelta(days=1)
    l = []
    for i in range(21):
        l.append((today+dt*i))

    return l
