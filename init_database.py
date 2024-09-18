import json
import os
from datetime import date
import argparse
import logging

from sqlmodel import Session
from passlib.hash import bcrypt

from database import *
from signable.entities.database_entities import (
    Users,
    Friends,
    Units,
    Lessons,
    LessonsInUnit,
    
    CameraQuestionsInLesson,
    CameraQuestions,

    MatchingQuestionsInLesson,
    MatchingQuestions,

    MultipleChoiceQuestionsInLesson,
    MultipleChoiceQuestions,
    
    FillInTheBlankQuestionsInLesson,
    FillInTheBlankQuestions,
    
    WatchToLearnQuestionsInLesson,
    WatchToLearnQuestions,
    
    Signs,
)


logging.getLogger('passlib').setLevel(logging.ERROR)

with open("signable/testing_data.json", "r") as json_file:
    DATA = json.load(json_file)


create_database()

## PARSE JSON TABLE REPRESNTATIONS HERE
## - EACH CLASS NEEDS TO BE PARSED (they are not all present right now)
with Session(engine) as session:
    users = [
        Users(
            **{
                **user_data,
                "created_at": date.fromisoformat(user_data["created_at"]),
                "password": bcrypt.hash("signable") # default password for default users
            }
        )
        for user_data in DATA["users"].values()
    ]

    xp = [
        UserXP(
            **{
                **xp_data,
                "day": date.fromisoformat(xp_data["day"])
            }
        )
        for xp_data in DATA["xp"].values()
    ]

    friends = [
        Friends(
            **{
                **friend_data
            }
        )
        for friend_data in DATA["friends"].values()
    ]

    units = [
        Units(
            **{
                **unit_data
            }
        )
        for unit_data in DATA["units"].values()
    ]

    lessons = [
        Lessons(
            **{
                **lesson_data
            }
        ) 
        for lesson_data in DATA["lessons"].values()
    ]

    lesson_unit_map = [
        LessonsInUnit(
            **{
                **lesson_unit_map_data
            }
        )
        for lesson_unit_map_data in DATA["lessons_in_unit"].values()
    ]

    signs = [
        Signs(
            **{
                **sign_data
            }
        )
        for sign_data in DATA["signs"].values()
    ]

    camera_questions = [
        CameraQuestions(
            **{
                **camera_question_data
            }
        )
        for camera_question_data in DATA["camera_questions"].values()
    ]

    camera_questions_map = [
        CameraQuestionsInLesson(
            **{
                **camera_questions_map_data
            }
        )
        for camera_questions_map_data in DATA["camera_questions_in_lesson"].values()
    ]

    multiple_choice_questions = [
        MultipleChoiceQuestions(
            **{
                **multiple_choice_question_data
            }
        )
        for multiple_choice_question_data in DATA["multiple_choice_questions"].values()
    ]

    multiple_choice_questions_map = [
        MultipleChoiceQuestionsInLesson(
            **{
                **multiple_choice_questions_map_data
            }
        )
        for multiple_choice_questions_map_data in DATA["multiple_choice_questions_in_lesson"].values()
    ]

    matching_questions = [
        MatchingQuestions(
            **{
                **matching_question_data
            }
        )
        for matching_question_data in DATA["matching_questions"].values()
    ]

    matching_questions_map = [
        MatchingQuestionsInLesson(
            **{
                **matching_question_map_data
            }
        )
        for matching_question_map_data in DATA["matching_questions_in_lesson"].values()
    ]

    fill_in_the_blank_questions = [
       FillInTheBlankQuestions(
           **{
               **fill_in_the_blank_question_data
           }
       )
       for fill_in_the_blank_question_data in DATA["fill_in_the_blank_questions"].values()
    ]

    fill_in_the_blank_questions_map = [
       FillInTheBlankQuestionsInLesson(
           **{
               **fill_in_the_blank_questions_map_data
           }
       )
       for fill_in_the_blank_questions_map_data in DATA["fill_in_the_blank_questions_in_lesson"].values()
    ]

    watch_to_learn_questions = [
        WatchToLearnQuestions(
            **{
                **watch_to_learn_data
            }
        )
        for watch_to_learn_data in DATA["watch_to_learn_questions"].values()
    ]

    watch_to_learn_questions_map = [
        WatchToLearnQuestionsInLesson(
            **{
                **watch_to_learn_map_data
            }
        )
        for watch_to_learn_map_data in DATA["watch_to_learn_questions_in_lesson"].values()
    ]

    table_data = [[Users, users],
                  [UserXP, xp],
                  [Friends, friends],
                  [Units, units],
                  [Lessons, lessons],
                  [LessonsInUnit, lesson_unit_map],
                  [Signs, signs],

                  [CameraQuestions, camera_questions],
                  [CameraQuestionsInLesson, camera_questions_map],

                  [MatchingQuestions, matching_questions],
                  [MatchingQuestionsInLesson, matching_questions_map],

                  [MultipleChoiceQuestions, multiple_choice_questions],
                  [MultipleChoiceQuestionsInLesson, multiple_choice_questions_map],

                  [FillInTheBlankQuestions, fill_in_the_blank_questions],
                  [FillInTheBlankQuestionsInLesson, fill_in_the_blank_questions_map],

                  [WatchToLearnQuestions, watch_to_learn_questions],
                  [WatchToLearnQuestionsInLesson, watch_to_learn_questions_map],
                 ]



    for table, rows in table_data:
        if not os.environ.get("PROD", False):
            session.add_all(rows)
        else:
            for row in rows:
                row = row.__dict__
                row.pop('_sa_instance_state', None)
                session.exec(table.__table__
                             .insert()
                             .prefix_with('IGNORE')
                             .values(row))
        session.commit()

