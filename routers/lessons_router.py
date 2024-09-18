from typing import Literal, Optional
from sqlmodel import Session
import random as rand

from fastapi import APIRouter, Depends

import database as db
from entities.lesson_entities import (
    LessonResponse,
    CameraQuestionResponse,   
    WatchToLearnQuestionResponse,   
    MultipleChoiceQuestionResponse,
    MatchingQuestionResponse,
    FillInTheBlankQuestionResponse,
    AnswerResponse, 
    UnitCollection,
    LessonCollection,
    QuestionCollection,
)
from entities.database_entities import LessonType, QuestionType

lessons_router = APIRouter(prefix="/units", tags=["Units"])

@lessons_router.get(path="/", response_model=UnitCollection)
def get_units(lower: int = 1, upper: Optional[int] = None, sort_by: Literal["unit_id"] = "unit_id", 
              session: Session = Depends(db.get_session),  ) -> UnitCollection:
    """
    Retrieve a range of Units based on unit id

    :param lower: An inclusive lower bound on unit ids of returned units \n
    :param upper: An inclusive upper bound on unit ids of returned units. If None, all units are returned \n
    :return: A collection containing the requested Units
    """
        
    sort_fn = lambda unit: getattr(unit, sort_by)
    units = sorted(db.get_units(session=session, lower=lower, upper=upper), key=sort_fn)
    meta = {"count": len(units)}

    return UnitCollection(meta=meta, units=units)


@lessons_router.get("/{unit_id}/lessons", response_model=LessonCollection)
def get_lessons(unit_id: int, session: Session = Depends(db.get_session), ) -> LessonCollection:
    """
    Retrieve all lessons in the Unit with the given unit_id

    :param unit_id: The unit to retrieve lessons from \n
    :return: A collection of all lessons in a unit \n
    """

    lessons = db.get_lessons_in_unit(session=session, unit_id=unit_id)
    meta = {"count": len(lessons)}

    return LessonCollection(meta=meta, lessons=lessons)


@lessons_router.get("/{lesson_id}/questions", response_model=QuestionCollection)
def get_questions(lesson_id: int, session: Session = Depends(db.get_session), ) -> QuestionCollection:
    """
    Retrieve all questions in a given lesson

    :param lesson_id: The id of the lesson to retrieve the questions from \n
    :return: A collection of Questions. Questions have various types denoted by their "question_type" field   
    """
    db_questions = db.get_questions_in_lesson(session=session, lesson_id=lesson_id)
    lesson = db.get_lesson_by_id(session=session, lesson_id=lesson_id)

    questions = []

    for question in db_questions:
        match question.question_type:
            case QuestionType.WATCH_TO_LEARN:
                 questions.append(
                     WatchToLearnQuestionResponse(question_id=question.question_id,
                                                  text=question.text,
                                                  question_type=question.question_type,
                                                  sign=question.sign,
                                                  starting_position=question.starting_position,
                                                  num_hands=question.num_hands,
                                                  motion=question.motion
                                                  )
                 )
            case QuestionType.CAMERA:
                questions.append(
                    CameraQuestionResponse(question_id=question.question_id,
                                           text=question.text,
                                           question_type=question.question_type,
                                           sign=question.sign,
                                           starting_position=question.starting_position,
                                           num_hands=question.num_hands,
                                           motion=question.motion
                                           )
                )
            case QuestionType.MULTIPLE_CHOICE:
                options = [db.ans_encode(option)
                           for option in 
                           [question.option_1, question.option_2, question.option_3, question.option_4]]

                rand.shuffle(options)

                questions.append(
                    MultipleChoiceQuestionResponse(question_id=question.question_id,
                                                   text=question.text,
                                                   question_type=question.question_type,
                                                   options=options
                                                   )
                )
            case QuestionType.MATCHING:
                text_options = list(filter(None, question.pairs.split(".")))
                image_options = [db.ans_encode(option) for option in text_options]

                rand.shuffle(text_options)
                rand.shuffle(image_options)

                questions.append(
                    MatchingQuestionResponse(question_id=question.question_id,
                                             text=question.text,
                                             question_type=question.question_type,
                                             image_options=image_options,
                                             text_options=text_options
                                             )
                )
            case QuestionType.FILL_IN_THE_BLANK:
                questions.append(
                    FillInTheBlankQuestionResponse(question_id=question.question_id,
                                                   text=question.text,
                                                   question_type=question.question_type,
                                                   image_path=db.ans_encode(question.image_path)
                                                   )
                )

    if lesson.lesson_type != LessonType.TEACH:
        rand.shuffle(questions)
    
    meta = {"count": len(questions)}
    return QuestionCollection(meta=meta, questions=questions)


@lessons_router.get(path="/{unit_id}/lessons/{lesson_id}", response_model=LessonResponse)
def get_lesson(unit_id: int, lesson_id: int, session: Session = Depends(db.get_session),  ) -> LessonResponse:
    """
    Retrieve a lesson from a unit by lesson id

    :param unit_id: The unit to retrieve lesson from \n
    :param lesson_id: The id of the lesson to retrieve \n
    :return: The lesson specified by id from a given unit
    """
    lesson = db.get_lesson_from_unit(session=session, unit_id=unit_id, lesson_id=lesson_id)

    return LessonResponse(lesson=lesson)


@lessons_router.get("/check-answer/{question_type}/{question_id}/{answer}", response_model=AnswerResponse)
def check_answer(question_type: QuestionType, question_id: int, answer: str, session: Session = Depends(db.get_session),  ) -> AnswerResponse:
    """
    Check a provided answer to a question against the database's held answer

    :param question_type: The type of the question being answered \n
    :param question_id: The id of the question being answered \n
    :param answer: The user-provided answer to the question \n
    :return: A response identifying the correctness of the provided answer
    """

    question = db.get_question(session=session, question_type=question_type, question_id=question_id)
    is_correct = False

    match question_type:
        case QuestionType.FILL_IN_THE_BLANK:
            actual = question.answer
            is_correct = answer.casefold() == actual.casefold()
        case QuestionType.MULTIPLE_CHOICE:
            actual = question.answer
            is_correct = db.ans_decode(answer).casefold() == actual.casefold()
        case QuestionType.MATCHING:
            pair = answer.split('.')
            image_name, text = db.ans_decode(pair[0]), pair[1]
            is_correct = text.upper() in question.pairs.upper() and image_name.casefold() == text.casefold()
        case _:
            pass # do nothing with unsupported q types for now

    return AnswerResponse(is_correct=is_correct)

