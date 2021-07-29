import discord
from discord.ext import commands, menus, tasks
from discord.ui import View, Button, Select
from discord.ext import commands, tasks
from extra.teacherDB import TeacherDB

from mysqldb import *
import asyncio

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


        # member = payload.member
        member = interaction.user

        embed = await self.teacher_classes_overview_embed(member)
        languages = await TeacherDB.get_taught_languages()
        # view = AddLessonView(languages)

        states = {}
        view = AddLessonView(states, embed, self.client, ['pt','en','de'])


        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        # if member.guild.id != server_id:
        #     await member.send(embed=discord.Embed(
        #     title='You\'re not allowed to do it!',
        #     description='In order to do that, you have first to become a member of [The Language Sloth Server](https://discord.gg/Dr9EkQph)!',
        #     color=discord.Colour.from_rgb(0,0,0)
        #     ))
        #     return
        # print('passei guild id')

        # if teacher_role_id not in [x.id for x in member.roles]:
        #     await member.send(embed=discord.Embed(
        #         title='You\'re not allowed to do that!',
        #         description='In order to do that, you have to be a Teacher.',
        #         color=discord.Colour.from_rgb(0,0,0)
        #     ).add_field(
        #         name='Apply to become a Teacher',
        #         value=f'Apply in the channel <#{report_channel_id}>'
        #     ))
        #     return
        print('passei teacher_role_id')

        # from now on create sequence of "menus.Menu" interactions here
        # so the teachers can work with the management pipelines

        # zeroth_msg = await member.send('Starting class management...')
        # zeroth_msg = await member.send('Starting class management...')
        # dm_ctx = await self.client.get_context(zeroth_msg)

        # pprint(dm_ctx.__dict__)
        # pprint(dm_ctx.author)
        # try:
        #     res = await ClassManagementMenuTeacher(dm_ctx, zeroth_msg, member).begin()
        # except:
        #     PrintException()




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


        # member = payload.member
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


        # member = payload.member
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
            self.add_disabled_btn(f"{states['selected_lang']}")

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
            self.add_disabled_btn(f"{states['selected_used_lang']}")

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
            self.add_disabled_btn(f"{['Extra','Permanent'][is_permanent]} class")

        if 'week_day' not in states:
            async def set_week_day(self):
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
            return
        else:
            self.add_disabled_btn(f"{states['week_day']}")

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
            self.add_disabled_btn(f"{time} h")


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
                self.add_disabled_btn(f"Not sent!", color=discord.ButtonStyle.red, row=1)




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

    if is_permanent:
        color=discord.Colour.from_rgb(234,72,223)
    else:
        color=discord.Colour.from_rgb(45,160,226)

    # embed = discord.Embed(title=f'{member.name}',
                          # description=f"Requested for adding {['an Extra','a Permanent'][states['is_permanent']]} class:", color=color
    embed = discord.Embed(
        title=f"Add {['Extra','Permanent'][is_permanent]} class request",
        description=f"Info:", color=color)
    embed.add_field(name='id',value=member.id)
    embed.add_field(name='name',value=member.name)
    embed.add_field(name='nick',value=member.nick)
    embed.add_field(name='language',value=states['selected_lang'])
    embed.add_field(name='language_used',value=states['selected_used_lang'])
    embed.add_field(name='day',value=states['week_day'])
    embed.add_field(name='time',value=states['time'])
    embed.add_field(name='permanent',value=is_permanent)

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

    embed = msg.embeds[0].to_dict()
    fields = {}
    for field in embed['fields']:
        fields[field['name']]=field['value']
    pprint(fields)

    inserted = False
    # NOTE: all fields in `fields` have strings as values
    if fields['permanent'] == 'True':
        inserted = await TeacherDB.insert_permanent_class(
            fields['id'], fields['name'], fields['language'], fields['language_used'], fields['day'], fields['time'], True
        )
    else:
        # await TeacherDB.insert_extra_class(
        #     fields['id'], fields['name'], fields['language'], fields['language_used'], fields['day'], fields['time'], True
        # )
        pass

    view = View(timeout=None)
    view.add_item(Button(
        disabled=True,
        style=discord.ButtonStyle.blurple if inserted else discord.ButtonStyle.red,
        label=f'Approved by {member.name}' if inserted else 'Class already exists!',
        emoji='\U0001F512'
    ))

    await interaction.response.edit_message(
        embed=msg.embeds[0],
        view=view
    )

    #TODO Add an result to the Teacher here and in deny
    pass

async def deny_new_class_request(self, interaction: discord.Interaction):
    member = interaction.user
    print('gostei desse babaca nao')
    msg = interaction.message
    view = View(timeout=None)
    view.add_item(Button(
        disabled=True,
        style=discord.ButtonStyle.blurple,
        label=f'Denied by {member.name}',
        emoji='\U0001F512'
    ))

    await interaction.response.edit_message(
        embed=msg.embeds[0],
        view=view
    )
    pass

async def feedback_teacher_request(member, txt):

    member
