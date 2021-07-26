import discord
from discord.ext import commands, menus, tasks
from extra.teacherDB import TeacherDB

from mysqldb import *
import asyncio

import linecache
import sys
from pprint import pprint

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


def dm_reaction_check(self, payload):
    # allowing to process only reactions from the msg author
    if payload.message_id != self.message.id or payload.user_id == self.msg.author.id:
        return False
    # removing the condition below from original code, bc
    # it prevents from working inside DMs when the message
    # didn't come from a Command
    # if payload.user_id not in {self.bot.owner_id, self._author_id, *self.bot.owner_ids}:
        # return False

    return payload.emoji in self.buttons


class ClassManagementMenuTeacherAdd(menus.MenuPages):
# class ClassManagementMenuTeacherAdd(menus.ListPageSource):
    ''' Class related to Class Management actions done by teachers '''

    # adicao
    # remocao
    # pausa
    # alteracao de horario

    reaction_check = dm_reaction_check

    def __init__(self, ctx: discord.ext.commands.Context, msg: discord.Message, member: discord.Member, current_classes: dict, languages: list):
    # def __init__(self, msg: discord.Message, member: discord.Member):
        self.current_classes = current_classes
        # self.languages = languages

        embed = self.teacher_classes_overview_embed()
        print('criei o embed')

        src  = ListTaughtLanguages(languages, embed)
        print('criei o source')

        super().__init__(source=src, timeout=60,delete_message_after=False,clear_reactions_after=True)
        print('dei init')

        self.member = member
        # self.content = content
        self.msg = msg
        self.ctx = ctx
        self.result = None


    def teacher_classes_overview_embed(self):
        embed = discord.Embed(
            title="**Adding Class Menu**",
            description="What do you want to do?\n\nYour current schedule is:",
            color=discord.Colour.from_rgb(234,72,223)
        )

        embed.add_field(
            name=':calendar_spiral: Permament classes',
            value=self.current_classes['permanent'],
            inline=False
        )
        embed.add_field(
            name=':calendar_spiral: Extra classes',
            value=self.current_classes['extra'],
            inline=False
        )
        embed.add_field(
            name=':notepad_spiral: **List of already taught languages**',
            value='',
            inline=False
        )
        embed.set_footer(
            text=':0 to 9: select language from listn\n:emojis do paginator:\n:emoji here: If your desired language is not listed'
        )


        return embed




    async def begin(self):
        await self.start(self.ctx, wait=True)
        # await self.start(self.ctx)
        return self.result


    async def finalize(self, timeout):

        embed = discord.Embed(
            title="**Thank you for teaching!**",
            description="Your requests, if any, were sent to the Lesson Management Team!\n\nYour latest schedule is:",
            color=discord.Colour.from_rgb(234,72,223)
        )
        # await self.teacher_classes_overview_embed(embed)

        # await self.changes_done(embed)
        # self.button_descriptions_embed(embed)

        # self.msg = await channel.send(embed=embed)
        await self.msg.edit(content=None, embed=embed)

    # async def changes_done(self, embed):
    #     yes   = ":white_check_mark:"
    #     no    = ":x:"
    #     maybe = ":hourglass:"
    #     yesno   = [no, yes]
    #     maybeno = [no, maybe]
    #
    #     changes_str = '\n'.join(
    #         [f'[{maybeno[x.status]}]: {x}' for x in self.changes['add']]+
    #         [f'[{maybeno[x.status]}]: {x}' for x in self.changes['edit']]+
    #         [f'[{yesno[x.status]}]: {x}' for x in self.changes['removal']]+
    #         [f'[{yesno[x.status]}]: {x}' for x in self.changes['pause']]+
    #     )
    #
    #     embed.add_field(
    #         name=':notebook_with_decorative_cover: Changes',
    #         values=changes_str,
    #         inline=False
    #     )
    #
    #     pass


    # # adicao - needs approval
    # @menus.button('\U0001F4E5')
    # async def do_add(self, payload):
    #     # self.show_available_slots(payload)
    #     pass
    #
    # # alteracao de horario - needs approval
    # @menus.button('\U0001F4C5')
    # async def do_edit(self, payload):
    #     pass
    #
    # # remocao - no approval
    # @menus.button('\U0001F4E4')
    # async def do_remove(self, payload):
    #     pass
    #
    # # pausa - no approval
    # @menus.button('\U000023F0')
    # async def do_pause(self, payload):
    #     pprint(payload)
    #     pass

    # # finalise
    # @menus.button('\U0001F44B')
    # async def do_stop(self, payload):
    #     pprint(payload)
    #     # print(payload.member)
    #     # await self.msg.edit(content=None)
    #     self.stop()
    #
    #     pass


class ListTaughtLanguages(menus.ListPageSource):
    """ A class for listing known languages. """

    def __init__(self, data, embed):
        """ Class initializing method. """
        data = data if len(data) else ["No taught languages yet. Please add yours."]

        super().__init__(data, per_page=5)
        print('passei do ListTaughtLanguages super init')
        self.embed = embed
        print('setei embed')

    def is_paginating(self) -> bool:
        """:class:`bool`: Whether pagination is required."""

        return True
        # return len(self.entries) > self.per_page

    async def format_page(self, menu, entries):
        """ Formats each page. """
        print('entrei format page')

        offset = menu.current_page * self.per_page
        print('format aqui', menu.current_page)
        pprint(self.embed.fields)
        val = '\n'.join([
            f'[{i}] {lang}' for i, lang in enumerate(entries)
        ])

        pprint(val)
        # self.embed.fields[2].value = val
        self.embed.set_field_at(
            index = 2,
            name = self.embed.fields[2].name,
            value = val,
            inline = self.embed.fields[2].inline
        )
        pprint(self.embed.fields)

        return self.embed
