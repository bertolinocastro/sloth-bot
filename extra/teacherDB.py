import asyncio
from mysqldb import *


class TeacherDB:

    @staticmethod
    async def get_teacher_classes(member_id):

        mycursor, db = await the_database()
        await mycursor.execute("SELECT language, day_of_week, time FROM PermanentClasses WHERE teacher_id = %s AND is_active" % (member_id))
        table_info = await mycursor.fetchall()
        await mycursor.close()

        ret = {
            'permanent':
                '\n'.join([f'[{l}]: {d}s at {t}:00' for l,d,t in table_info]) if table_info else 'Empty',
            'extra': ' Empty' # TODO: implement extra classes database
        }
        return ret


    @staticmethod
    async def get_taught_languages():

        mycursor, db = await the_database()
        print(mycursor, db)
        await mycursor.execute("SELECT DISTINCT(language) FROM PermanentClasses")
        print('executei')
        # TODO: implement ExtraClasses calls
        # await mycursor.execute("SELECT UNIQUE(language) FROM ExtraClasses")
        table_info = await mycursor.fetchall()
        print('dei fetch all\n', table_info)
        await mycursor.close()
        print('closeei')

        # flattening
        ret = [x[0] for x in table_info]
        print('flatenei')

        return ret
