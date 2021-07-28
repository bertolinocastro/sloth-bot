import asyncio
from mysqldb import *


class TeacherDB:

    @staticmethod
    async def create_permanent_classes_table():

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE PermanentClasses (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                teacher_id BIGINT NOT NULL,
                teacher_name VARCHAR(100) NOT NULL,
                language VARCHAR(50) NOT NULL,
                language_taught VARCHAR(50) NOT NULL,
                day_of_week ENUM('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'),
                time TINYINT UNSIGNED NOT NULL,
                is_active BOOL NOT NULL,
                date_of_creation DATE NOT NULL DEFAULT NOW(),
                date_of_inactivation DATE)""")
                # day_of_week TINYINT UNSIGNED NOT NULL,
        await db.commit()
        await mycursor.close()


    @staticmethod
    async def create_permanent_classes_occurrences_table():

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


    @staticmethod
    async def table_exists(table: str):
        table_info = await TeacherDB.fetchall(
            f"SHOW TABLE STATUS LIKE '{table}'"
        )
        return len(table_info) != 0

    @staticmethod
    async def fetchall(query : str):
        mycursor, db = await the_database()
        await mycursor.execute(query)
        table_info = await mycursor.fetchall()
        await mycursor.close()
        return table_info


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


    @staticmethod
    async def get_available_hours(selected_lang, is_permanent, week_day):
        assert is_permanent, "Must implement extra classes in the database first!"
        #TODO: implement this diagnosis with classes that are close to the next day or to the previous day by 1 hour

        table_info = await TeacherDB.fetchall(
            f"SELECT DISTINCT(time) FROM {'PermanentClasses' if is_permanent else 'ExtraClasses'} WHERE language = '{selected_lang}' AND day_of_week = '{week_day}' AND is_active = TRUE"
        )
        #TODO: implement the limitation of 3 classes at the same time on the same day

        ret = sorted([x[0] for x in table_info])
        day = range(0, 24)
        for time in ret:
            day.remove(time)
            day.remove(time-1)
            day.remove(time+1)


        return day
