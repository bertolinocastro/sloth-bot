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


class ClassManagementMenuTeacher(menus.MenuPages):
    ''' Class related to Class Management actions done by teachers '''

    reaction_check = dm_reaction_check

    # def prepare(self):
        # self.override_skip_pagination()

    def __init__(self, ctx: discord.ext.commands.Context, msg: discord.Message, member: discord.Member):
    # def __init__(self, msg: discord.Message, member: discord.Member):
        try:
            super().__init__(source=ListTaughtLanguages(),timeout=60,delete_message_after=False,clear_reactions_after=True)
        except:
            PrintException()
        self.member = member
        # self.content = content
        self.msg = msg
        self.ctx = ctx
        self.result = None
        self.changes = {}
        self.current_classes = {}
        self.languages = []
        self.back_status = []
        print(self.source)


    async def begin(self):
        await self.start(self.ctx, wait=True)
        # await self.main_menu()
        return self.result

    def should_add_reactions(self):
        return True


    # ============================
    #    Misc
    # ============================

    async def teacher_classes_overview_embed(self, embed):

        classes = await TeacherDB.get_teacher_classes(self.member.id)
        self.current_classes = classes
        # pprint(classes)

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


    # async def set_buttons(self, emojis, callbacks):
    #     for i,j in zip(emojis, callbacks):
    #         try:
    #             # if self.__tasks:
    #             await self.add_button(button=menus.Button(i, j), react=True)
    #             # else:
    #                 # self.add_button(button=menus.Button(i, j), react=False)
    #         except:
    #             PrintException()
    #             print(i,j)
    #             self.add_button(button=menus.Button(i, j), react=False)
    #         # self.__tasks

    async def update_buttons(self, mode):
        mb = lambda x, e=True: {y.__menu_button__ for y in x if e}
        mf = lambda x, e=True: {y for y in x if e}

        pag_btns = mf([self.go_to_first_page, self.go_to_previous_page, self.go_to_next_page, self.go_to_last_page], len(self.languages))

        self.btns = {
            'main': {self.do_add, self.do_edit, self.do_remove, self.do_pause, self.do_stop},
            'add': {self.do_stop} | pag_btns,
            'edit': {},
            'remove': {},
            'pause': {}
        }

        # __menu_button__
        rem = set(self.buttons.keys())-mb(self.btns[mode])
        add = self.btns[mode]-set(self.buttons.items())
        for btn in rem:
            print(btn, 'rem')
            await self.remove_button(btn, react=True)
        for btn, emj in zip(add,mb(add)):
            print(btn, emj, 'add')
            await self.add_button(menus.Button(emj, btn), react=True)

        pass


    # =================================
    #   overriding pagination skip_if
    # =================================

    def _skip_pagination(self):
        return not len(self.back_status)

    def _skip_double_triangle_buttons(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages <= 2 and self._skip_pagination()

    @menus.button('\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f',
            # position=First(0), skip_if=_skip_pagination)
            skip_if=_skip_pagination)
    async def go_to_first_page(self, payload):
        """go to the first page"""
        await self.show_page(0)

    # @menus.button('\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f', position=First(1), skip_if=_skip_pagination)
    @menus.button('\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f', skip_if=_skip_pagination)
    async def go_to_previous_page(self, payload):
        """go to the previous page"""
        await self.show_checked_page(self.current_page - 1)

    # @menus.button('\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f', position=Last(0), skip_if=_skip_pagination)
    @menus.button('\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f', skip_if=_skip_pagination)
    async def go_to_next_page(self, payload):
        """go to the next page"""
        await self.show_checked_page(self.current_page + 1)

    @menus.button('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f',
            # position=Last(1), skip_if=_skip_pagination)
            skip_if=_skip_pagination)
    async def go_to_last_page(self, payload):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        await self.show_page(self._source.get_max_pages() - 1)

    # @menus.button('\N{BLACK SQUARE FOR STOP}\ufe0f', position=Last(2), skip_if=_skip_pagination)
    # @menus.button('\N{BLACK SQUARE FOR STOP}\ufe0f', skip_if=_skip_pagination)
    @menus.button('\N{BLACK SQUARE FOR STOP}\ufe0f', skip_if=lambda x: True)
    async def stop_pages(self, payload):
        """stops the pagination session."""
        # self.stop()
        pass


    # =================================
    #   main menu
    # =================================

    async def send_initial_message(self, ctx, channel):
        await self.main_menu()
        return self.msg

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



    async def main_menu(self):

        embed = discord.Embed(
            title="**You called me in the class management channel.**",
            description="What do you want to do?\n\nYour current schedule is:",
            color=discord.Colour.from_rgb(234,72,223)
        )
        await self.teacher_classes_overview_embed(embed)

        embed.set_footer(
            text='\U0001F4E5 add a class\t\U0001F4E4 remove a class\n\U0001F4C5 edit a class\t\U000023F0 pause classes'
        )

        await self.msg.edit(content=None, embed=embed)

        # emojis = ['\U0001F4E5', '\U0001F4C5', '\U0001F4E4', '\U000023F0', '\U0001F44B']
        # callbacks = [self.do_add, self.do_edit, self.do_remove, self.do_pause, self.do_stop]
        # await self.set_buttons(emojis, callbacks)


    def _skip_main(self):
        return len(self.back_status)

    # adicao - needs approval
    @menus.button('\U0001F4E5', skip_if=_skip_main)
    async def do_add(self, payload):
        self.changes['add'] = await self.add_menu()

        # self.show_available_slots(payload)

        # self.changes['add'] = await ClassManagementMenuTeacherAdd(self.ctx, self.msg, self.member, self.current_classes, languages).begin()

    # alteracao de horario - needs approval
    @menus.button('\U0001F4C5', skip_if=_skip_main)
    async def do_edit(self, payload):
        pass

    # remocao - no approval
    @menus.button('\U0001F4E4', skip_if=_skip_main)
    async def do_remove(self, payload):
        pass

    # pausa - no approval
    @menus.button('\U000023F0', skip_if=_skip_main)
    async def do_pause(self, payload):
        pprint(payload)
        pass

    # finalise
    @menus.button('\U0001F44B', skip_if=_skip_main)
    async def do_stop(self, payload):
        if len(self.back_status):
            self.back_status[-1]()
        else:
            self.stop()


    # =================================
    #   add menu
    # =================================

    async def add_menu(self):
        try:
            await self.update_buttons('add')
        except:
            PrintException()

        self.back_status.append(self.main_menu)

        self.languages = await TeacherDB.get_taught_languages()

        embed = self.add_menu_embed()
        src  = ListTaughtLanguages(self.languages, embed)
        await self.change_source(src)




    def add_menu_embed(self):
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


    # async def show_page(self, ctx, channel):
    #     page = await self._source.get_page(0)
    #     kwargs = await self._get_kwargs_from_page(page)
    #     # return await channel.send(**kwargs)
    #     return await self.msg.edit(**kwargs)

    # async def finalize(self, timeout):
    #
    #     embed = discord.Embed(
    #         title="**Thank you for teaching!**",
    #         description="Your requests, if any, were sent to the Lesson Management Team!\n\nYour latest schedule is:",
    #         color=discord.Colour.from_rgb(234,72,223)
    #     )
    #     # await self.teacher_classes_overview_embed(embed)
    #
    #     # await self.changes_done(embed)
    #     # self.button_descriptions_embed(embed)
    #
    #     # self.msg = await channel.send(embed=embed)
    #     await self.msg.edit(content=None, embed=embed)

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

    def __init__(self, data=[], embed=None):
        """ Class initializing method. """
        data = data if len(data) else ["No taught languages yet. Please add yours."]

        super().__init__(data, per_page=5)
        # print('passei do ListTaughtLanguages super init')
        self.embed = embed
        # print('setei embed')


    async def format_page(self, menu, entries):
        """ Formats each page. """
        # print('entrei format page')

        offset = menu.current_page * self.per_page
        # print('format aqui', menu.current_page)
        # pprint(self.embed.fields)
        val = '\n'.join([
            f'[{i}] {lang}' for i, lang in enumerate(entries)
        ])

        # pprint(val)
        # self.embed.fields[2].value = val
        self.embed.set_field_at(
            index = 2,
            name = self.embed.fields[2].name,
            value = val,
            inline = self.embed.fields[2].inline
        )
        # pprint(self.embed.fields)

        return self.embed
