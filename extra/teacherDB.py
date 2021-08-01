import asyncio
from mysqldb import *
from pprint import pprint


class TeacherDB:

    @staticmethod
    async def drop_table(table):
        mycursor, db = await the_database()
        await mycursor.execute(f"DROP TABLE {table}")
        await db.commit()
        await mycursor.close()


    @staticmethod
    async def create_permanent_classes_table():

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE PermanentClasses (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                teacher_id BIGINT NOT NULL,
                teacher_name VARCHAR(100) NOT NULL,
                language VARCHAR(50) NOT NULL,
                language_used VARCHAR(50) NOT NULL,
                day_of_week ENUM('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday') NOT NULL,
                time TINYINT UNSIGNED NOT NULL,
                is_active BOOL NOT NULL,
                date_of_creation DATE NOT NULL DEFAULT (CURRENT_DATE),
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
                type ENUM('Hosted','Missed','Cancelled','Paused') NOT NULL
                details VARCHAR(150),
                FOREIGN KEY (permanent_class_id) REFERENCES PermanentClasses(id)
            )
            """)
                # type TINYINT NOT NULL,
        await db.commit()
        await mycursor.close()


    @staticmethod
    async def create_extra_classes_table():

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE ExtraClasses (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                teacher_id BIGINT NOT NULL,
                teacher_name VARCHAR(100) NOT NULL,
                language VARCHAR(50) NOT NULL,
                language_used VARCHAR(50) NOT NULL,
                time TINYINT UNSIGNED NOT NULL,
                date_of_creation DATE NOT NULL DEFAULT (CURRENT_DATE),
                date_to_occur DATE NOT NULL)""")
        await db.commit()
        await mycursor.close()


    @staticmethod
    async def create_lesson_approval_requests_table():

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE LessonApprovalRequests (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                teacher_id BIGINT NOT NULL,
                teacher_name VARCHAR(100) NOT NULL,
                language VARCHAR(50) NOT NULL,
                language_used VARCHAR(50) NOT NULL,
                day_of_week ENUM('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday') NOT NULL,
                time TINYINT UNSIGNED NOT NULL,
                is_permanent BOOL NOT NULL,
                datetime_of_request DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
                date_to_occur DATE,
                message_id BIGINT NOT NULL)""")
        await db.commit()
        await mycursor.close()


    @staticmethod
    async def insert_lesson_approval_request(teacher_id, teacher_name, language, language_used, day_of_week, time, is_permanent, message_id, date_to_occur=None):
        mycursor, db = await the_database()
        # query below is the same in get_similar_lesson_approval_request
        await mycursor.execute("""
            SELECT EXISTS(SELECT * FROM LessonApprovalRequests WHERE teacher_id = %s AND language = %s AND language_used = %s AND day_of_week = %s AND time = %s AND is_permanent = %s AND date_to_occur = %s AND TIMESTAMPDIFF(DAY, datetime_of_request,NOW()) < 1)
            """, (teacher_id, language, language_used, day_of_week, time, is_permanent, date_to_occur))
        exist = await mycursor.fetchall()
        if exist[0][0]:
            await mycursor.close()
            return None
        await mycursor.execute("""
            INSERT INTO LessonApprovalRequests (teacher_id, teacher_name, language, language_used, day_of_week, time, is_permanent, date_to_occur, message_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", (teacher_id, teacher_name, language, language_used, day_of_week, time, is_permanent, date_to_occur, message_id))
        last_id = mycursor.lastrowid
        await db.commit()
        await mycursor.close()
        return last_id


    @staticmethod
    async def update_msg_id_lesson_approval_request(id, message_id):
        mycursor, db = await the_database()
        await mycursor.execute("""
        UPDATE LessonApprovalRequests
            SET message_id = %s
            WHERE id = %s
        """, (message_id, id))
        await db.commit()
        await mycursor.close()


    @staticmethod
    async def get_similar_lesson_approval_request(teacher_id, language, language_used, day_of_week, time, is_permanent, date_to_occur):
        """Getting a similar request that was sent within the last 24h."""

        mycursor, db = await the_database()
        await mycursor.execute("""
            SELECT EXISTS(SELECT * FROM LessonApprovalRequests WHERE teacher_id = %s AND language = %s AND language_used = %s AND day_of_week = %s AND time = %s AND is_permanent = %s AND date_to_occur = %s AND TIMESTAMPDIFF(DAY, datetime_of_request,NOW()) < 1)
            """, (teacher_id, language, language_used, day_of_week, time, is_permanent, date_to_occur))
        exist = await mycursor.fetchall()
        await mycursor.close()
        return exist[0][0]


    # @staticmethod
    # async def define_procedure_for_generic_class_insertion():
    #     mycursor, db = await the_database()
    #     await mycursor.execute("CREATE TEMPORARY TABLE record SELECT * FROM LessonApprovalRequests WHERE message_id = %s; SELECT is_permanent FROM record", (message_id,))
    #     pass


    @staticmethod
    async def approve_permanent_class_request(message_id):

        mycursor, db = await the_database()
        try:
            await db.begin()
            # await mycursor.execute("CREATE TEMPORARY TABLE record SELECT * FROM LessonApprovalRequests WHERE message_id = %s; SELECT is_permanent FROM record", (message_id,))
            # is_permanent = await mycursor.fetchall()
            # print('criou temp')
            # pprint(is_permanent)
            await mycursor.execute("""
                INSERT INTO PermanentClasses (teacher_id, teacher_name, language, language_used, day_of_week, time, is_active)
                    SELECT teacher_id, teacher_name, language, language_used, day_of_week, time, TRUE
                    FROM LessonApprovalRequests WHERE message_id = %s AND is_permanent = TRUE;

                INSERT INTO ExtraClasses (teacher_id, teacher_name, language, language_used, time, date_to_occur)
                    SELECT teacher_id, teacher_name, language, language_used, time, date_to_occur
                    FROM LessonApprovalRequests WHERE message_id = %s AND is_permanent = FALSE""", (message_id, message_id))
            # # if is_permanent[0][0]:
            #     await mycursor.execute("""
            #         INSERT INTO PermanentClasses (teacher_id, teacher_name, language, language_used, day_of_week, time, is_active)
            #             SELECT teacher_id, teacher_name, language, language_used, day_of_week, time, TRUE
            #             FROM record""")
            # # else:
            #     await mycursor.execute("""
            #         INSERT INTO ExtraClasses (teacher_id, teacher_name, language, language_used, time, date_to_occur)
            #             SELECT teacher_id, teacher_name, language, language_used, time, date_to_occur
            #             FROM record""")

            # await mycursor.execute("PREPARE insert_generic FROM 'INSERT IGNORE INTO ?(teacher_id, teacher_name, language, language_used, day_of_week, time, is_active) SELECT * FROM record'", (message_id,))
            # print('criou preparou')
            # await mycursor.execute(
            #     """
            #     EXECUTE insert_generic USING IF((SELECT is_permanent FROM record LIMIT 1) <> 0, 'PermanentClasses', 'ExtraClasses')
            #     """)
            # print('executou')
            # await mycursor.execute('DEALLOCATE PREPARE insert_generic')
            print('dealocou')
            # await mycursor.execute(
            #     """
            #     INSERT INTO PermanentClasses (teacher_id, teacher_name, language, language_used, day_of_week, time, is_active)
            #         SELECT teacher_id, teacher_name, language, language_used, day_of_week, time, TRUE
            #         FROM LessonApprovalRequests
            #         WHERE message_id = %s""", (message_id,))
            await mycursor.execute("""
                DELETE FROM LessonApprovalRequests
                    WHERE message_id = %s""", (message_id,))
        except Exception as e:
            print('ERRO DO SATANÁS ', e)
            await db.rollback()
            ret = False
        else:
            await db.commit()
            ret = True
        finally:
            await mycursor.close()
        return ret


    @staticmethod
    async def deny_class_request(message_id):
        mycursor, db = await the_database()
        await mycursor.execute("""
            DELETE FROM LessonApprovalRequests
                WHERE message_id = %s""", (message_id,))
        await db.commit()
        await mycursor.close()



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
        # NOTE: we are getting the data for now only for the target language ENGLISH but it can be taken  based on teacher's  roles for other target languages as well
        await mycursor.execute("SELECT DISTINCT(is_written_like) FROM Languages WHERE target_language = 'English'")
        table_info = await mycursor.fetchall()
        await mycursor.close()

        # flattening
        ret = [x[0] for x in table_info]

        return ret


    @staticmethod
    async def get_available_hours(selected_lang, selected_used_lang, is_permanent, week_day, date_to_occur=None, **kwargs):
        """Extra class must set date_to_occur"""

        # assert is_permanent, "Must implement extra classes in the database first!"
        # TODO: urgent-> this isn't working with extra classes!

        #TODO: implement this diagnosis with classes that are close to the next day or to the previous day by 1 hour

        # TODO: implement what muffin said about different classes with different used_languages
        # "if is_permanent else 'ExtraClasses'"
        table_info = await TeacherDB.fetchall(
            f"SELECT DISTINCT(time) FROM PermanentClasses WHERE language = '{selected_lang}' AND day_of_week = '{week_day}' AND is_active = TRUE"
        )
        #TODO: implement the limitation of 3 classes at the same time on the same day

        ret = sorted([x[0] for x in table_info])
        day = list(range(0, 24))
        for time in ret:
            for d in [-1,0,1]:
                try:
                    day.remove(time+d)
                except: # trying to prevent from ValueError when the loop already removed the same number from the list
                    pass


        return day

    @staticmethod
    async def insert_permanent_class(teacher_id, teacher_name, language, language_used, day_of_week, time, is_active):
        mycursor, db = await the_database()
        await mycursor.execute("""
            SELECT EXISTS(SELECT * FROM PermanentClasses WHERE language = %s AND language_used = %s AND day_of_week = %s AND time = %s AND is_active = TRUE)
            """, (language, language_used, day_of_week, time))
        exist = await mycursor.fetchall()
        if exist[0][0]:
            await mycursor.close()
            return False
        # return
        await mycursor.execute("""
            INSERT INTO PermanentClasses (teacher_id, teacher_name, language, language_used, day_of_week, time, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""", (teacher_id, teacher_name, language, language_used, day_of_week, time, is_active))
        await db.commit()
        await mycursor.close()
        return True


    @staticmethod
    async def create_languages_table():
        mycursor, db = await the_database()
        # this works like a graph (adjacency matrix)
        # 1st column: origin language (in english)
        # 2nd column: target language (in english)
        # 3rd column: the actual name of origin language written in the target language
        await mycursor.execute("""
            CREATE TABLE Languages (
                origin_language VARCHAR(50) NOT NULL,
                target_language VARCHAR(50) NOT NULL,
                is_written_like VARCHAR(50) NOT NULL,
                UNIQUE(origin_language, target_language, is_written_like))""")
        await db.commit()
        await mycursor.close()


    @staticmethod
    async def insert_prelisted_languages_table():

        langs = "('Afrikaans','English','Afrikaans'), ('Albanian','English','Albanian'), ('Amazigh','English','Amazigh'), ('Amharic','English','Amharic'), ('Arabic','English','Arabic'), ('Armenian','English','Armenian'), ('Azerbaijani','English','Azerbaijani'), ('Balkan Languages','English','Balkan Languages'), ('Basque','English','Basque'), ('Belarusian','English','Belarusian'), ('Bulgarian','English','Bulgarian'), ('Cantonese','English','Cantonese'), ('Catalan','English','Catalan'), ('Cebuano/Bisaya','English','Cebuano/Bisaya'), ('Celtic','English','Celtic'), ('Conlangs','English','Conlangs'), ('Cosmic','English','Cosmic'), ('Czech-Slovak','English','Czech-Slovak'), ('Danish','English','Danish'), ('Dutch','English','Dutch'), ('English','English','English'), ('Estonian','English','Estonian'), ('Faroese','English','Faroese'), ('Farsi','English','Farsi'), ('Filipino','English','Filipino'), ('Finnish','English','Finnish'), ('French','English','French'), ('Georgian','English','Georgian'), ('German','English','German'), ('Greek','English','Greek'), ('Hebrew','English','Hebrew'), ('Hindustani','English','Hindustani'), ('Hungarian','English','Hungarian'), ('Icelandic','English','Icelandic'), ('Indigenous languages','English','Indigenous languages'), ('Indonesian','English','Indonesian'), ('Italian','English','Italian'), ('Japanese','English','Japanese'), ('Kazakh','English','Kazakh'), ('Khmer','English','Khmer'), ('Korean','English','Korean'), ('Kurdish','English','Kurdish'), ('Latin','English','Latin'), ('Latvian','English','Latvian'), ('Lithuanian','English','Lithuanian'), ('Luxembourgish','English','Luxembourgish'), ('Macedonian','English','Macedonian'), ('Malay','English','Malay'), ('Mandarin','English','Mandarin'), ('Mongolian','English','Mongolian'), ('Norwegian','English','Norwegian'), ('Pashto','English','Pashto'), ('Polish','English','Polish'), ('Portuguese','English','Portuguese'), ('Romanian','English','Romanian'), ('Russian','English','Russian'), ('Slovenian','English','Slovenian'), ('South Asian Languages','English','South Asian Languages'), ('Spanish','English','Spanish'), ('Sub-Saharan languages','English','Sub-Saharan languages'), ('Swedish','English','Swedish'), ('Thai','English','Thai'), ('Turkic Languages','English','Turkic Languages'), ('Turkish','English','Turkish'), ('Ukrainian','English','Ukrainian'), ('Vietnamese','English','Vietnamese')"

        mycursor, db = await the_database()
        await mycursor.execute("""
            INSERT INTO Languages (origin_language, target_language, is_written_like)
            VALUES """+langs)
        await db.commit()
        await mycursor.close()
