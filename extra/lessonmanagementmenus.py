import discord
from discord.ext import commands, menus, tasks
from discord.ui import View, Button, Select
from discord.ext import commands, tasks
from extra.teacherDB import TeacherDB
from extra.calendarapi import Calendar

from mysqldb import *
import asyncio

from datetime import date, timedelta, datetime
from pytz import timezone

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


    async def teacher_classes_overview_embed(self, member, ret_classes=None):

        perma, extra = await TeacherDB.get_teacher_classes(member.id)

        if ret_classes is not None:
            ret_classes['permanent'] = [{'class_id':i,'language':l,'language_used':u,'day_of_week':d,'time':t} for i,l,u,d,t in perma]

            ret_classes['extra'] = [{'class_id':i,'language':l,'language_used':u,'date_to_occur':d,'time':t} for i,l,u,d,t in extra]


        perma_str = '\n'.join([f'{j}) {l} in {u}: {d}s at {ampm_time(t)}' for j,(i,l,u,d,t) in enumerate(perma)]) if perma else 'Empty'

        extra_str = '\n'.join([f'{j}) {l} in {u}: {d.strftime("%A, %d of %B")} at {ampm_time(t)}' for j,(i,l,u,d,t) in enumerate(extra)]) if extra else 'Empty'

        embed = discord.Embed(
            title="**Your current schedule is:**",
            description="",
            color=discord.Colour.from_rgb(234,72,223)
        )

        if perma is None and extra is None:
            embed.add_field(
                name=':calendar_spiral: You have no classes registered!',
                value='Please ask lesson management to work with it out',
                inline=False
            )
            return embed

        embed.add_field(
            name=':calendar_spiral: Permament classes',
            value=perma_str,
            inline=False
        )
        embed.add_field(
            name=':calendar_spiral: Extra classes',
            value=extra_str,
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

        langroles = [x.name.replace('Native ','').replace('Fluent ','').replace('Studying ','') for x in member.roles if x.name.startswith('Native') or x.name.startswith('Fluent') or x.name.startswith('Studying') or x.name.startswith('Programming') or x.name.startswith('Sign Languages')]

        languages = [x for x in languages if x in langroles]

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

        await interaction.response.send_message('pause/cancel', ephemeral=True)

        await Calendar.test()



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

        classes = {}
        embed = await self.teacher_classes_overview_embed(member, ret_classes=classes)

        request = {}
        view = DelLessonView(request, embed, self.client, classes)


        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)



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

        if 'language' not in states:
            async def set_language(self):
                self.states['language'] = self.values[0]

            for i in range(0, len(langs), 25):
                self.add_item(
                    # LangsSelect(
                    ClassManagementSelect(
                        states,
                        embed,
                        langs,
                        func=set_language,
                        client=client,
                        constructor=AddLessonView,
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
            self.add_disabled_btn(f"Teaching {states['language']}")

        if 'language_used' not in states:
            async def set_language_used(self):
                self.states['language_used'] = self.values[0]

            for i in range(0, len(langs), 25):
                self.add_item(
                    # LangsSelect(
                    ClassManagementSelect(
                        states,
                        embed,
                        langs,
                        func=set_language_used,
                        client=client,
                        constructor=AddLessonView,
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
            self.add_disabled_btn(f"in {states['language_used']}")

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
                    constructor=AddLessonView,
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

        if 'day_of_week' not in states and 'date_to_occur' not in states:
            if states['is_permanent']:
                async def set_week_day(self):
                    self.states['date_to_occur'] = None
                    self.states['day_of_week'] = self.values[0]
                    times = await TeacherDB.get_available_hours(**self.states)
                    self.states['times'] = times

                self.add_item(
                    ClassManagementSelect(
                        states,
                        embed,
                        langs,
                        func=set_week_day,
                        client=client,
                        constructor=AddLessonView,
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
                    self.states['day_of_week'] = d.strftime("%A")
                    times = await TeacherDB.get_available_hours(**self.states)
                    self.states['times'] = times

                self.add_item(
                    ClassManagementSelect(
                        states,
                        embed,
                        langs,
                        func=set_date_to_occur,
                        client=client,
                        constructor=AddLessonView,
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
                self.add_disabled_btn(f"on {states['day_of_week']}s")
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
                    constructor=AddLessonView,
                    placeholder='Select an available time',
                    row=1,
                    options=[
                        discord.SelectOption(
                            # label=str(value)+' h',
                            label=ampm_time(value),
                            value=value
                        )
                        for value in states['times']
                    ]
                )
            )
            return
        else:
            time = states['time']
            self.add_disabled_btn(f"at {ampm_time(time)}")


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
                fdbk = states['not_ok_feedback']
                self.add_disabled_btn(f"Not sent!{' '+fdbk if fdbk else ''}", color=discord.ButtonStyle.red, row=1)


class DelLessonView(View):

    def add_disabled_btn(self, label, row=None, color=discord.ButtonStyle.blurple, emoji=None):
        self.add_item(Button(
            disabled=True,
            style=color,
            label=label,
            row=row,
            emoji=emoji
        ))


    def __init__(self, request, embed, client, classes):
        super().__init__(timeout=120)

        if 'is_permanent' not in request:

            async def set_is_permanent(self):
                self.states['is_permanent'] = self.values[0] == 'True'

            self.add_item(
                ClassManagementSelect(
                    request,
                    embed,
                    classes,
                    func=set_is_permanent,
                    client=client,
                    constructor=DelLessonView,
                    placeholder='Is it a permanent class?',
                    row=0,
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
            is_permanent = request['is_permanent']
            self.add_disabled_btn(f"Deleting the {['extra','permanent'][is_permanent]} classes:")

        is_permanent = request['is_permanent']

        if 'class_indexes' not in request:
            async def set_class(self):
                self.states['class_indexes'] = self.values

            mykey = 'permanent' if is_permanent else 'extra'
            opts = classes[mykey][:25] # limiting up to 25 entries, bc I'm lazy to code any workaround for teachers with more than 25 classes (which is definitely uncommon tbh)
            pprint(opts)

            self.add_item(
                ClassManagementSelect(
                    request,
                    embed,
                    classes,
                    func=set_class,
                    client=client,
                    constructor=DelLessonView,
                    placeholder='Select a class to delete',
                    max_values=len(opts),
                    options=[
                        discord.SelectOption(
                            label=i
                        )
                        for i, value in enumerate(opts)
                    ]
                )
            )
            return
        else:
            for i in request['class_indexes']:
                self.add_disabled_btn(i)

        if '1st_check' not in request:
            self.add_item(CLMVConfirm(
                request,
                embed,
                client=client,
                langs=classes,
                func=del_class_1st_check_yes,
                style=discord.ButtonStyle.grey,
                label='Delete class?',
                emoji='\U0001F625',
                row=1
            ))
            self.add_item(CLMVConfirm(
                request,
                embed,
                client=client,
                langs=classes,
                func=del_class_1st_check_no,
                style=discord.ButtonStyle.red,
                label='STOP',
                emoji='\U0001F590',
                row=1
            ))
            return
        else:
            if not request['1st_check']:
                self.add_disabled_btn(f"Thanks!", color=discord.ButtonStyle.green, row=1, emoji='\U0001F973')
                return

        if 'ok' not in request :
            self.add_item(CLMVConfirm(
                request,
                embed,
                client=client,
                langs=classes,
                func=continue_del_class_request,
                style=discord.ButtonStyle.blurple,
                label='Yes, I\'m sure!',
                emoji='\U0001F62D',
                row=1
            ))
            self.add_item(CLMVConfirm(
                request,
                embed,
                client=client,
                langs=classes,
                func=cancel_del_class_request,
                style=discord.ButtonStyle.red,
                label='No, I regret!',
                emoji='\U0001F97A',
                row=1
            ))
        else:
            if request['ok']:
                self.add_disabled_btn(f"Deleted", color=discord.ButtonStyle.green, row=1)
            else:
                fdbk = request['not_ok_feedback']
                self.add_disabled_btn(f"Not deleted!{' '+fdbk if fdbk else ''}", color=discord.ButtonStyle.red, row=1, emoji='\U0001F973')



class ClassManagementSelect(Select):
    def __init__(self, states, embed, langs, client, func, constructor, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.states = states
        self.embed = embed
        self.langs = langs
        self.func = func
        self.client = client

        def wrapper(states, embed, client, langs):
            return constructor(states, embed, client, langs)
        self.constructor = wrapper

    async def callback(self, interaction: discord.Interaction):
        await self.func(self)

        await interaction.response.edit_message(
            embed=self.embed,
            view=self.constructor(
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

    # has_similar = await TeacherDB.get_similar_lesson_approval_request(member.id, states['language'], states['language_used'], states['day_of_week'], states['time'], is_permanent)

    # setting 0 as message_id because the message was not sent yet
    # if you send the message into thhe approval channel, you can use here
    # the message id. This will prevent from using the lastrowid property
    # within the embed without having to send+edit the discord message
    states['id'] = await TeacherDB.insert_lesson_approval_request(member.id, member.name, states['language'], states['language_used'], states['day_of_week'], states['time'], states['is_permanent'], 0, states['date_to_occur'])

    if states['id'] is None:
        states['ok'] = False
        states['not_ok_feedback'] = "There's still a similar recent request you sent under review!"

        await interaction.response.edit_message(
            embed=self.embed,
            view=AddLessonView(
                states,
                self.embed,
                self.client,
                langs=self.langs
            )
        )
        return

    states['ok'] = True

    await interaction.response.edit_message(
        embed=self.embed,
        view=AddLessonView(
            states,
            self.embed,
            self.client,
            langs=self.langs
        )
    )

    await send_request_in_approval_channel(states, member, self.client, self.langs)


async def send_request_in_approval_channel(states, member, client, langs=None):

    # | teacher_id         | teacher_name | language  | language_used | day_of_week | time | is_permanent | datetime_of_request | date_to_occur |


    if states['is_permanent']:
        color=discord.Colour.from_rgb(234,72,223)
    else:
        color=discord.Colour.from_rgb(45,160,226)


    # langroles = [x.name for x in member.roles if x.name.startswith('Native') or x.name.startswith('Fluent')]
    # langroles_str = '**'+'**,**'.join(langroles)+'**' if len(langroles) else ''

    # nick = "**"+member.nick+"**" if member.nick else ''

    # the key below is set inside the DB call get_class_request and get_all_class_requests
    timestamp = states['datetime_of_request'] if 'datetime_of_request' in states else None

    embed = discord.Embed(
        title=f"Request #{states['id']}:\t\t\t\t\t\tAdd {['Extra','Permanent'][states['is_permanent']]} class",
        description=f"<@{member.id}> wants to add a new class",
        color=color, timestamp=timestamp)



    time_str = f", {states['date_to_occur_pretty']}" if not states['is_permanent'] else ''

    embed.add_field(name='Class Info:',value=f"Language: {states['language']}\nIn: {states['language_used']}\nTime: {ampm_time(states['time'])} {states['day_of_week']}"+time_str, inline=False)

    # NOTE: below are prettier and human-friendlier texts
    # ..... don't delete them, bc we might need to use them back
    # if states['is_permanent']:
    #     embed.add_field(name='Class Info:',value=f"They want to teach **{states['language']}** using **{states['language_used']}**\n at **{states['time']}:00** __every__ **{states['day_of_week']}**", inline=False)
    # else:
    #     embed.add_field(name='Class Info:',value=f"They want to teach **{states['language']}** using **{states['language_used']}**\n at **{states['time']}:00** __on__ **{states['date_to_occur_pretty']}, {states['day_of_week']}**", inline=False)


    # embed.add_field(name='Teacher Info',value=f"Server nick: {nick}\nAccount nick: **{member.name}**\nRoles: {langroles_str}", inline=False)

    embed.set_footer(text="Check the TLS Tracker for any inconsistences the bot couldn't get")

    embed.set_thumbnail(url=member.avatar.url)
    embed.set_author(name='Link to TLS Tracker', url=f"https://thelanguagesloth.com/tracker", icon_url='https://thelanguagesloth.com/static/assets/images/favicon.png')


    view = View(timeout=None)
    view.add_item(CLMVConfirm(
        custom_id='approve_new_class_request_id',
        states=states,
        embed=embed,
        client=client,
        langs=langs,
        func=approve_new_class_request,
        style=discord.ButtonStyle.green,
        label='Approve',
        emoji='\U00002705'
    ))
    view.add_item(CLMVConfirm(
        custom_id='deny_new_class_request_id',
        states=states,
        embed=embed,
        client=client,
        langs=langs,
        func=deny_new_class_request,
        style=discord.ButtonStyle.red,
        label='Deny',
        emoji='\U0001F590'
    ))

    app_channel = client.get_channel(class_management_approval_channel_id)
    msg = await app_channel.send(embed=embed, view=view)

    await TeacherDB.update_msg_id_lesson_approval_request(states['id'], msg.id)

    request = await TeacherDB.get_class_request(msg.id)
    event = await Calendar.add_class(request, to_be_approved=True)



async def cancel_new_class_request(self, interaction: discord.Interaction):
    self.states['ok'] = False
    self.states['not_ok_feedback'] = ''

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

    request = await TeacherDB.get_class_request(msg.id)
    if request is not None:
        inserted = await TeacherDB.approve_class_request(msg.id)

    btnstyle = discord.ButtonStyle.grey if request is None else discord.ButtonStyle.blurple if inserted else discord.ButtonStyle.red
    btnlabel = "This message isn't associated with a request anymore!" if request is None else f'Approved by {member.name}' if inserted else 'Some error ocurred!'

    view = View(timeout=None)
    view.add_item(Button(
        disabled=True,
        style=btnstyle,
        label=btnlabel,
        emoji='\U0001F512'
    ))

    await interaction.response.edit_message(
        embed=msg.embeds[0],
        view=view
    )

    if request is None:
        return

    event = await Calendar.add_class(request)

    extend_request_as_in_view(request)

    embed = discord.Embed(
        title=f"Approved Request #{request['id']}:\t\t\tAdd {['Extra','Permanent'][request['is_permanent']]} class",
        description=f"We are happy to inform that your request was approved!\n\nYou can look it in [TLS calendar](https://thelanguagesloth.com/class/calendar/)\n\nIf you have any questions, please, contact the Lesson Management Team <#here> (= some general channel)",
        color=discord.Colour.from_rgb(46,242,52))

    await feedback_teacher_request_embed(embed, request)

    try:
        await member.send(embed=embed)
    except discord.errors.Forbidden as e:
        print(f'Member {member.name} has blocked their DM')
        pass



async def deny_new_class_request(self, interaction: discord.Interaction):
    member = interaction.user
    msg = interaction.message

    request = await TeacherDB.get_class_request(msg.id)
    if request is not None:
        deleted = await TeacherDB.deny_class_request(msg.id)

    btnstyle = discord.ButtonStyle.grey if request is None else discord.ButtonStyle.red
    btnlabel = "This message isn't associated with a request anymore!" if request is None else f'Denied by {member.name}'

    view = View(timeout=None)
    view.add_item(Button(
        disabled=True,
        style=btnstyle,
        label=btnlabel,
        emoji='\U0001F512'
    ))

    await interaction.response.edit_message(
        embed=msg.embeds[0],
        view=view
    )

    if request is None:
        return

    extend_request_as_in_view(request)

    thread_name = f"Denied Add #{request['id']}"

    thread = await create_thread_with_teacher(msg, member, thread_name)

    embed = discord.Embed(
        title=f"Denied Request #{request['id']}:\t\t\tAdd {['Extra','Permanent'][request['is_permanent']]} class",
        description=f"We are sorry to inform that your request was denied.\n\nPlease review your request and check [TLS calendar](https://thelanguagesloth.com/class/calendar/) to solve probable conflicting class hours. __Remember: all classes are in CET time zone.__\n\nGet in touch with the Lesson Management Team here <#{thread.id}>",
        color=discord.Colour.from_rgb(219,104,98))

    await feedback_teacher_request_embed(embed, request)

    try:
        await member.send(embed=embed)
    except discord.errors.Forbidden as e:
        print(f'Member {member.name} has blocked their DM')
        pass


async def feedback_teacher_request_embed(embed, states):

    if states['is_permanent']:
        embed.add_field(name='Request Info:',value=f"You wanted to teach **{states['language']}** using **{states['language_used']}**\n at **{ampm_time(states['time'])}** __every__ **{states['day_of_week']}**", inline=False)
    else:
        embed.add_field(name='Request Info:',value=f"You wanted to teach **{states['language']}** using **{states['language_used']}**\n at **{ampm_time(states['time'])}** __on__ **{states['date_to_occur_pretty']}, {states['day_of_week']}**", inline=False)


    # embed.add_field(name='Teacher Info',value=f"Server nick: {nick}\nAccount nick: **{member.name}**\nRoles: {langroles_str}", inline=False)

    # embed.set_footer(text="Check the TLS Calendar to make sure your request fits the schedule")

    # embed.set_thumbnail(url=member.avatar.url)
    # embed.set_author(name='Link to TLS Calendar', url=f"https://thelanguagesloth.com/calendar", icon_url='https://thelanguagesloth.com/static/assets/images/favicon.png')
    pass


async def create_thread_with_teacher(msg, member, name):
    channel = msg.channel

    welcome_text = f"{member.mention} <@&{lesson_management_role_id}>"

    try:
        # PRIVATE WAY

        # DNK: make things in a private thread?
        # .... I think we test it before, because maybe letting them
        # .... might allow other teachers to help and improve the environment
        thread = await channel.start_thread(name=name)
        # await thread.add_user(member)


    except discord.errors.HTTPException as e:
        # PUBLIC WAY

        # NOTE: I'm creating another message with the embed, because there's no way of getting the message that created a thread after this point, not even by reading the history, so we simply copy the same embed into the thread's first message. This way, even when the administrator purges the approval channel, there will still be information about the request in the thread

        # thread = await msg.start_thread(name=name)

        reply = await msg.reply('Opening a thread!')
        thread = await reply.start_thread(name=name)

    await thread.send(content=welcome_text, embed=msg.embeds[0])
    # await thread.send(content=welcome_text, embeds=msg.embeds, view=View.from_message(msg, timeout=0))

    return thread


def get_future_dates():

    today = datetime.now(timezone('Europe/Berlin')).date()
    dt = timedelta(days=1)
    l = []
    for i in range(21):
        l.append((today+dt*i))

    return l

def extend_request_as_in_view(request):
    if not request['is_permanent']:
        # d = date.fromisoformat(request['date_to_occur'])
        d = request['date_to_occur']
        request['date_to_occur_pretty'] = d.strftime("%d of %B")
    pass

def ampm_time(time: int):
    time = int(time)
    return f"{time%12 or 12}" + ("AM" if time<12 else "PM")



async def continue_del_class_request(self, interaction: discord.Interaction):
    member = interaction.user

    states = self.states
    is_permanent = states['is_permanent']

    ids = [self.langs['permanent' if is_permanent else 'extra'][int(i)]['class_id'] for i in states['class_indexes']]
    pprint(ids)

    states['ok'] = await TeacherDB.delete_class(is_permanent, ids=ids)

    states['not_ok_feedback'] = "Failed to delete" if not states['ok'] else ''

    await interaction.response.edit_message(
        embed=self.embed,
        view=DelLessonView(
            states,
            self.embed,
            self.client,
            classes=self.langs
        )
    )


async def cancel_del_class_request(self, interaction: discord.Interaction):
    self.states['ok'] = False
    self.states['not_ok_feedback'] = ''

    await interaction.response.edit_message(
        embed=self.embed,
        view=DelLessonView(
            self.states,
            self.embed,
            self.client,
            classes=self.langs
        )
    )

async def del_class_1st_check_yes(self, interaction):
    self.states['1st_check'] = True

    await interaction.response.edit_message(
        embed=self.embed,
        view=DelLessonView(
            self.states,
            self.embed,
            self.client,
            classes=self.langs
        )
    )

async def del_class_1st_check_no(self, interaction):
    self.states['1st_check'] = False

    await interaction.response.edit_message(
        embed=self.embed,
        view=DelLessonView(
            self.states,
            self.embed,
            self.client,
            classes=self.langs
        )
    )
