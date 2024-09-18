from datetime import date, datetime
import enum
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel


##                ##
##      Meta      ##
##                ##

class LessonType(enum.IntEnum):
    TEACH = 0
    PRACTICE = 1
    TEST = 2


class QuestionType(enum.IntEnum):
    CAMERA = 0
    MULTIPLE_CHOICE = 1
    MATCHING = 2
    FILL_IN_THE_BLANK = 3
    WATCH_TO_LEARN = 4



##                       ##
##    Linking Models     ##
##                       ##

class Friends(SQLModel, table=True):
    """
    Defines a "friend" relationship between users

    :link: Users
    :link: Users
    """
    __tablename__ = "friends"
    
    follower_id: Optional[int] = Field(default=None, primary_key=True, foreign_key="users.user_id")
    followed_id: Optional[int] = Field(default=None, primary_key=True, foreign_key="users.user_id")


class LessonsInUnit(SQLModel, table=True):
    """
    Defines the lessons contained in a unit

    :link: Units
    :link: Lessons
    """
    __tablename__ = "lessons_in_unit"

    unit_id: int = Field(primary_key=True, foreign_key="units.unit_id")
    lesson_id: int = Field(foreign_key="lessons.lesson_id")
    lesson_index: int = Field(primary_key=True)


class RecognizersInLessons(SQLModel, table=True):
    """
    Defines the recognizer models used by a lesson

    :link: Lessons
    :link: Recognizers
    """
    __tablename__ = "recognizers_in_lessons"

    lesson_id: int = Field(primary_key=True, foreign_key="lessons.lesson_id")
    recognizer_id: int = Field(primary_key=True, foreign_key="recognizers.recognizer_id")


class CameraQuestionsInLesson(SQLModel, table=True):
    """
    Defines the camera questions contained in a lesson
    
    :link: Lessons
    :link: CameraQuestions
    """
    __tablename__ = "camera_questions_in_lesson"

    lesson_id: int = Field(primary_key=True, foreign_key="lessons.lesson_id")
    question_id: int = Field(primary_key=True, foreign_key="camera_questions.question_id")  


class MultipleChoiceQuestionsInLesson(SQLModel, table=True):
    """
    Defines the multiple choice questions contained in a lesson
    
    :link: Lessons
    :link: MultipleChoiceQuestions
    """
    __tablename__ = "multiple_choice_questions_in_lesson"

    lesson_id: int = Field(primary_key=True, foreign_key="lessons.lesson_id")
    question_id: int = Field(primary_key=True, foreign_key="multiple_choice_questions.question_id")


class MatchingQuestionsInLesson(SQLModel, table=True):
    """
    Defines the matching questions contained in a lesson

    :link: Lessons
    :link: MatchingQuestions
    """
    
    __tablename__ = "matching_questions_in_lesson"

    lesson_id: int = Field(primary_key=True, foreign_key="lessons.lesson_id")
    question_id: int = Field(primary_key=True, foreign_key="matching_questions.question_id")


class FillInTheBlankQuestionsInLesson(SQLModel, table=True):
   """
   Defines the fill-in-the-blank questions contained in a lesson
    
   :link: Lessons
   :link: FillInTheBlankQuestions
   """
   __tablename__ = "fill_in_the_blank_questions_in_lesson"

   lesson_id: int = Field(primary_key=True, foreign_key="lessons.lesson_id")
   question_id: int = Field(primary_key=True, foreign_key="fill_in_the_blank_questions.question_id")


class WatchToLearnQuestionsInLesson(SQLModel, table=True):
   """
   Defines the watch-to-learn questions contained in a lesson
    
   :link: Lessons
   :link: WatchToLearnQuestions
   """
   __tablename__ = "watch_to_learn_questions_in_lesson"

   lesson_id: int = Field(primary_key=True, foreign_key="lessons.lesson_id")
   question_id: int = Field(primary_key=True, foreign_key="watch_to_learn_questions.question_id")  



##                       ##
##   User Relationships  ##
##                       ##

class Users(SQLModel, table=True):
    """ 
    Defines system Users 
    """
    __tablename__ = "users"

    # meta
    user_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: date = Field(default_factory=datetime.today)
    password: str
    
    # profile
    username: str = Field(unique=True)
    email: str = Field(unique=True)
    first_name: Optional[str] = Field(default="")
    last_name: Optional[str] = Field(default="")

    # progress
    unit_progress: int = Field(default=0)
    lesson_index: int = Field(default=0)
    days_logged: int = Field(default=0)

    # permissions
    is_admin: bool = Field(default=False)

    followers: List["Users"] = Relationship(
        back_populates="following",
        link_model=Friends,
        sa_relationship_kwargs=dict(
            primaryjoin="Users.user_id==Friends.followed_id",
            secondaryjoin="Users.user_id==Friends.follower_id",
        ),
    )
    following: List["Users"] = Relationship(
        back_populates="followers",
        link_model=Friends,
        sa_relationship_kwargs=dict(
            primaryjoin="Users.user_id==Friends.follower_id",
            secondaryjoin="Users.user_id==Friends.followed_id",
        ),
    )



##                        ##
##  Lesson Relationships  ## 
##                        ##

class Units(SQLModel, table=True):
    """ 
    Defines a collection of Lessons 
    """ 
    __tablename__ = "units"

    unit_id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    lesson_count: int = Field(default=0)

    lessons: List["Lessons"] = Relationship(
        back_populates="units", 
        link_model=LessonsInUnit
    )


class Lessons(SQLModel, table=True):
    """ 
    Defines a set of Questions 
    """
    __tablename__ = "lessons"

    lesson_id: Optional[int] = Field(default=None, primary_key=True)
    lesson_type: LessonType
    title: str
    question_count: int = Field(default=0)

    # meta
    units: List["Units"] = Relationship(
        back_populates="lessons", 
        link_model=LessonsInUnit
    )
    recognizers: List["Recognizers"] = Relationship(
        back_populates="lessons", 
        link_model=RecognizersInLessons
    )

    # learning questions
    watch_to_learn_questions: List["WatchToLearnQuestions"] = Relationship(
       back_populates="lessons",
       link_model=WatchToLearnQuestionsInLesson
    )

    # quiz questions
    camera_questions: List["CameraQuestions"] = Relationship(
        back_populates="lessons", 
        link_model=CameraQuestionsInLesson
    )
    multiple_choice_questions: List["MultipleChoiceQuestions"] = Relationship(
        back_populates="lessons",
        link_model=MultipleChoiceQuestionsInLesson
    )
    matching_questions: List["MatchingQuestions"] = Relationship(
       back_populates="lessons",
       link_model=MatchingQuestionsInLesson
    )
    fill_in_the_blank_questions: List["FillInTheBlankQuestions"] = Relationship(
        back_populates="lessons",
        link_model=FillInTheBlankQuestionsInLesson
    )



##                          ##
##  Question Relationships  ## 
##                          ##

class CameraQuestions(SQLModel, table=True):
    """ 
    Defines a Question that recognizes a gesture signed by a User
    """
    __tablename__ = "camera_questions"

    question_id: Optional[int] = Field(default=None, primary_key=True)
    question_type: QuestionType = QuestionType.CAMERA 
    text: str

    sign: Optional[str] = Field(default=None, foreign_key="signs.sign")
    starting_position: str # is this a sign?
    num_hands: int
    motion: bool
   
    lessons: List["Lessons"] = Relationship(
        back_populates="camera_questions", 
        link_model=CameraQuestionsInLesson
    )


class MultipleChoiceQuestions(SQLModel, table=True):
    """
    Defines a multiple choice question
    """
    __tablename__ = "multiple_choice_questions"

    question_id: Optional[int] = Field(default=None, primary_key=True)
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    text: str

    option_1: Optional[str] = Field(default=None, foreign_key="signs.sign")
    option_2: Optional[str] = Field(default=None, foreign_key="signs.sign")
    option_3: Optional[str] = Field(default=None, foreign_key="signs.sign")
    option_4: Optional[str] = Field(default=None, foreign_key="signs.sign")
    answer: Optional[str] = Field(default=None, foreign_key="signs.sign")

    lessons: List["Lessons"] = Relationship(
        back_populates="multiple_choice_questions",
        link_model=MultipleChoiceQuestionsInLesson
    )


class MatchingQuestions(SQLModel, table=True):
    """
    Defines a mathcing question
    """

    __tablename__ = "matching_questions"

    question_id: Optional[int] = Field(default=None, primary_key=True)
    question_type: QuestionType = QuestionType.MATCHING
    text: str

    pairs: str

    lessons: List["Lessons"] = Relationship(
        back_populates="matching_questions",
        link_model=MatchingQuestionsInLesson
    )


class FillInTheBlankQuestions(SQLModel, table=True):
    """
    Defines a fill-in-the-blank question
    """
    __tablename__ = "fill_in_the_blank_questions"

    question_id: Optional[int] = Field(default=None, primary_key=True)
    question_type: QuestionType = QuestionType.FILL_IN_THE_BLANK
    text: str

    image_path: str
    answer: Optional[str] = Field(default=None, foreign_key="signs.sign")

    lessons: List["Lessons"] = Relationship(
        back_populates="fill_in_the_blank_questions",
        link_model=FillInTheBlankQuestionsInLesson
    )


class WatchToLearnQuestions(SQLModel, table=True):
    """
    Defines a Question that shows how to sign a word or character
    """

    __tablename__ = "watch_to_learn_questions"

    question_id: Optional[int] = Field(default=None, primary_key=True)
    question_type: QuestionType = QuestionType.WATCH_TO_LEARN 
    text: str

    sign: Optional[str] = Field(default=None, foreign_key="signs.sign")
    starting_position: str # is this a sign?
    num_hands: int
    motion: bool

    lessons: List["Lessons"] = Relationship(
        back_populates="watch_to_learn_questions", 
        link_model=WatchToLearnQuestionsInLesson
    )



##                ##
##    Resources   ##
##                ##

class Signs(SQLModel, table=True):
    """
    Defines a general representation of an ASL gesture 
    """
    __tablename__ = "signs"

    sign: str = Field(primary_key=True)
    image_path: str = Field(default="")


class Recognizers(SQLModel, table=True):
    """ 
    Defines a gesture recognizer model
    """
    __tablename__ = "recognizers"

    recognizer_id: Optional[int] = Field(default=None, primary_key=True)

    lessons: List["Lessons"] = Relationship(
        back_populates="recognizers",
        link_model=RecognizersInLessons,
        sa_relationship_kwargs={"cascade": "delete"}
    )


class UserXP(SQLModel, table=True):
    """
    Tracks user xp on a day-to-day basis
    """

    __tablename__ = "user_xp"

    user_id: int = Field(primary_key=True, foreign_key="users.user_id")
    day: date = Field(primary_key=True, default_factory=date.today)
    xp: int = Field(default=0)




