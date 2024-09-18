from pydantic import BaseModel
from sqlmodel import SQLModel

from typing import List, Union

from signable.entities.resource_entities import Metadata
from signable.entities.database_entities import LessonType, QuestionType

##                  ##
##      Models      ##
##                  ##

class UnitModel(SQLModel):
    """
    API definition of a unit
    """

    unit_id: int
    title: str
    description: str
    lesson_count: int


class LessonInUnitModel(SQLModel):
    """
    API Definition of a lesson/unit relationship
    """

    unit_id: int
    lesson_id: int
    lesson_index: int


class LessonModel(SQLModel):
    """
    API definition of a lesson
    """

    lesson_id: int
    title: str
    lesson_type: LessonType
    question_count: int


class QuestionInLessonModel(SQLModel):
    """
    API Definition of a question/lesson relationship
    """
    
    lesson_id: int
    question_type: QuestionType
    question_id: int


class CameraQuestionModel(SQLModel):    
    """
    API definition of a camera question
    """

    question_id: int
    sign: str 
    starting_position: str 
    num_hands: int
    motion: bool


class WatchToLearnQuestionModel(SQLModel):    
    """
    API definition of a watch-to-learn question
    """

    question_id: int
    sign: str 
    starting_position: str 
    num_hands: int
    motion: bool


class MultipleChoieQuestionModel(SQLModel):    
    """
    API definition of a multiple choice question
    """

    question_id: int
    text: str
    question_type: str
    option_1: str
    option_2: str
    option_3: str
    option_4: str
    answer: str


class MatchingQuestionModel(SQLModel):
    """
    API definition of a matching question
    """

    question_id: int
    text: str
    question_type: str
    pairs: str


class FillInTheBlankQuestionModel(SQLModel):    
    """
    API definition of a fill-in-the-blank question
    """

    question_id: int
    text: str
    question_type: str
    image_path: str   # TODO - Does *not* need an image path in DB
    answer: str
 

class SignModel(SQLModel):
    """
    API definition of a sign
    """

    sign: str
    image_path: str



##                              ##
##     Creations / Updates      ##
##                              ##


class AddWatchQuestion(BaseModel):
    """
    Create a new WatchToLearn question
    """

    text: str
    sign: str
    starting_position: str
    num_hands: int
    motion: bool


class AddCameraQuestion(BaseModel):
    """
    Create a new SignToCamera question
    """

    text: str
    sign: str
    starting_position: str
    num_hands: int
    motion: bool


class AddMultipleChoicQuestion(BaseModel):
    """
    Create a new MultipleChoice question
    """

    text: str
    options: List[str]
    answer: str


class AddFillInTheBlankQuestion(BaseModel):
    """
    Create a new FillInTheBlank question
    """
 
    text: str
    image_path: str
    answer: str


class AddMatchingQuestion(BaseModel):
    """
    Create a new Matching question
    """

    text: str
    pairs: str


class AddLesson(BaseModel):
    """
    Create a new Lesson
    """

    lesson_type: LessonType
    title: str


class UpdateQuestionInLesson(BaseModel):
    """
    Add a question to a lesson
    """

    lesson_id: int
    question_type: QuestionType
    question_id: int


class AddUnit(BaseModel):
    """
    Create a new Unit
    """  

    title: str
    description: str


class UpdateLessonInUnit(BaseModel):
    """
    Add a lesson to a unit
    """

    unit_id: int
    lesson_id: int
    lesson_index: int


class CreateSign(BaseModel):
    """
    API Reuest format for creating a Sign
    """

    sign : str


class UpdateSign(BaseModel):
    """
    API Reuest format for updating a Sign
    """

    sign_key: str
    image_path: str



##                     ##
##      Responses      ##
##                     ##

class UnitResponse(BaseModel):
    """
    API Response for a single unit
    """

    unit: UnitModel


class LessonInUnitResponse(BaseModel):
    """
    API Response for an update lesson/unit relationship
    """

    msg: str
    details: LessonInUnitModel
    

class LessonResponse(BaseModel):
    """
    API Response for a single lesson
    """

    lesson: LessonModel


class QuestionInLessonResponse(BaseModel):
    """
    API Response for an updated question/lesson relationship
    """
    
    msg: str
    details: QuestionInLessonModel


class QuestionResponse(BaseModel):
    """
    API Definition of a generalized question
    """

    question_id: int
    question_type: QuestionType
    text: str


class CameraQuestionResponse(QuestionResponse):
    """
    API Response for a "sign to camera" question
    """

    sign: str
    starting_position: str
    num_hands: int
    motion: bool


class MultipleChoiceQuestionResponse(QuestionResponse):
    """
    API Response for displaying a multiple choice question
    """
    
    options: List[str]


class MatchingQuestionResponse(QuestionResponse):
    """
    API Response for displaying a matching question
    """

    image_options: List[str]
    text_options: List[str]


class FillInTheBlankQuestionResponse(QuestionResponse):
    """
    API Response for displaying a fill in the blank question
    """

    image_path: str


class WatchToLearnQuestionResponse(QuestionResponse):
    """
    API Response for displaying a watch to learn question
    """

    sign: str
    starting_position: str
    num_hands: int
    motion: bool


class AnswerResponse(BaseModel):
    """
    API Response for a user-provided answer
    """

    is_correct: bool


class SignResponse(BaseModel):
    """
    API Response for a Sign
    """

    msg: str
    sign: SignModel



##                      ##
##      Collections     ##
##                      ##

class UnitCollection(BaseModel):
    """
    API Response for a collection of Units 
    """

    meta: Metadata
    units: List[UnitModel]


class LessonCollection(BaseModel):
    """
    API Response for a collection of Lessons
    """

    meta: Metadata
    lessons: List[LessonModel]


class QuestionCollection(BaseModel):
    """
    API Response for a collection of generalized Questions
    """

    meta: Metadata
    questions: List[Union[CameraQuestionResponse,
                          MultipleChoiceQuestionResponse,
                          MatchingQuestionResponse,
                          FillInTheBlankQuestionResponse,
                          WatchToLearnQuestionResponse
                          ]]
