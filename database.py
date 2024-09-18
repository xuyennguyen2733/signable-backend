import os
from typing import List, Optional

from datetime import date
from typing import List, Optional
from sqlalchemy import func, text
from sqlmodel import (
    Session, 
    SQLModel,
    create_engine, 
    select
)

from entities.lesson_entities import (
    AddCameraQuestion, 
    AddFillInTheBlankQuestion, 
    AddLesson, AddMatchingQuestion, 
    AddMultipleChoicQuestion,
    AddUnit,
    AddWatchQuestion, 
    CreateSign,
    QuestionInLessonModel,
    UpdateLessonInUnit,
    UpdateQuestionInLesson,
    UpdateSign, 
)

from entities.user_entities import ProgressUpdate, XpResponse, UserRegistration, UserUpdate
from entities.database_entities import (
    QuestionType,
    UserXP,
    Users,
    Friends,
    Units,
    Lessons,
    LessonsInUnit,

    CameraQuestions,
    CameraQuestionsInLesson,
    
    MultipleChoiceQuestions,
    MultipleChoiceQuestionsInLesson,
    
    MatchingQuestions,
    MatchingQuestionsInLesson,
    
    FillInTheBlankQuestions,
    FillInTheBlankQuestionsInLesson,
    
    WatchToLearnQuestions,
    WatchToLearnQuestionsInLesson,
    
    Signs,
)

# Maps "question type table" to "question type linking table"
question_tables = { 
                    WatchToLearnQuestions: WatchToLearnQuestionsInLesson,
                    CameraQuestions: CameraQuestionsInLesson,
                    MultipleChoiceQuestions: MultipleChoiceQuestionsInLesson,
                    FillInTheBlankQuestions: FillInTheBlankQuestionsInLesson,
                    MatchingQuestions: MatchingQuestionsInLesson,
                  }

if os.environ.get("PROD", "False") == "True":
    USERNAME = os.environ['DB_USER']
    PASSWORD = os.environ['DB_PASS']
    ENDPOINT = os.environ['DB_ENDPOINT']
    PORT = os.environ['DB_PORT']

    if os.environ.get("TEST_DB", "False") == "True":
        NAME = os.environ['TEST_DB_NAME']
    else:
        NAME = os.environ['DB_NAME']

    db_uri = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{ENDPOINT}:{PORT}/{NAME}"

    engine = create_engine(db_uri)
else: 
    engine = create_engine(
        "sqlite:///testing_db.db",
        echo=False,
        connect_args={"check_same_thread": False,},
    )


def create_database():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session



##                  ##
##    Exceptions    ##
##                  ##

class EntityNotFoundException(Exception):
    """
    Entity is not contained in database
    """

    def __init__(self, *args, entity_name: str, entity_id: object) -> None:
        self.entity_name = entity_name
        self.entity_id = entity_id


class UnrelatedEntitiesException(Exception):
    """
    No association between two existing entites in database
    """

    def __init__(self, *args, first_name: str, second_name: str, first_id: object, second_id: object) -> None:
        self.first_entity = first_name
        self.second_entity = second_name
        self.first_id = first_id
        self.second_id = second_id


class InvalidRequestExcpetion(Exception):
    """
    Entity request is not allowed or supported
    """

    def __init__(self, *args, entity_name: str, msg: str) -> None:
        self.entity_name = entity_name
        self.msg = msg


class PermissionsException(Exception):
    """
    Raised for unauthorized api requests
    """

    def __init__(self) -> None:
        pass


class DuplicateEntitiyException(Exception):
    """
    A provided entity to create already exists in the database
    """

    def __init__(self, *args, entity_name: str, entity_id: str) -> None:
        self.entity_name = entity_name
        self.entity_id = entity_id



##                 ##
##      Users      ##
##                 ##

def create_user(session: Session, registration: UserRegistration) -> Users:
    """
    Create a new User and add it to the database

    :param session: The database session
    :param user_data: The Users object containing user data
    :return: The newly created User
    """

    user = Users(
        password=registration.password,
        username=registration.username,
        email=registration.email,
        first_name=registration.first_name,
        last_name=registration.last_name,
    )    
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


def delete_user(session, user_id):
    """
    Delete a user from the database
    
    :param user_id: The id of the user to delete
    """

    # TODO Remove the user from all "friend" relationships
    # TODO delete the user

    pass


def get_user_by_id(session: Session, user_id: int) -> Users:
    """
    Get a User from the database by user id

    :param user_id: The id of the requested User
    :raises EntityNotFoundException: No such User id
    :return: The corresponsing User
    """
    
    user = session.get(Users, user_id)
    if user:
        return user
    raise EntityNotFoundException(entity_name="User", entity_id=user_id)


def get_user_by_username(session: Session, username: str) -> Users:
    """
    Get a User from the database by username
    """
    user = session.exec(select(Users).where(Users.username == username)).first()
    
    if user:
        return user
    
    raise EntityNotFoundException(entity_name="User", entity_id=username)


def reset_password(session: Session, username: str, password: str) -> Users:
    """
    Reset a user's password
    """
    user = get_user_by_username(session, username)
    if (user):
        setattr(user, "password", password)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def get_authenticated_user(session: Session, username: str) -> Users:
    # Query the database to see if there is any user with the provided username
    user = session.exec(select(Users).where(Users.username == username)).first()
    if not user:
        return False
    
    return user


def search_for_new_friends(user_id: int, search_query: str, session: Session) -> List[Users]:
    searched_friends = session.exec(select(Users).where(Users.username.startswith(search_query))).all()
    return searched_friends


def add_friend(user_id: int, new_friend_id: int, session: Session ) -> Users:
    user = get_user_by_id(session, user_id)
    # curr_friends = get_followers_by_id(session, user_id)
    
    if new_friend_id == user_id:
        raise ValueError("You cannot add yourself as a friend")
    
    new = Friends(
        follower_id=new_friend_id,
        followed_id=user_id    
    )    
    session.add(new)
    
    try:
        session.commit()
        # session.refresh(new)
    except Exception as e:
        session.rollback()  # Roll back the transaction
        print("Commit failed:", e) #Faling here, not adding new user to database
        return user
    return user


def delete_friend(user_id: int, old_friend_id: int, session: Session ) -> Users:
        removed_friend = get_user_by_id(session, old_friend_id)
        remove_friend = session.exec(select(Friends).where(Friends.followed_id == user_id).where(Friends.follower_id == old_friend_id)).first()
        session.delete(remove_friend)
        session.commit()
        return removed_friend


def get_followers_by_id(session: Session, user_id: int) -> List[Users]:
    """
    Get a all followers of a given User from the database by user id

    :param user_id: The id of the requested User
    :return: A list of all Users following the given User
    """

     # Select follower ids
    get_follower_ids = select(Friends.follower_id).where(Friends.followed_id == user_id)

    # Fetch follower ids
    follower_ids = [follower_id for (follower_id) in session.exec(get_follower_ids)]

    # Select followers based on follower ids
    get_followers = select(Users).where(Users.user_id.in_(follower_ids))

    # Fetch followers
    followers = session.exec(get_followers).all()
    
    return followers


def update_user_progress(session: Session, user: Users, details: ProgressUpdate) -> bool:
    """
    Update a user's progression
    """

    user = get_user_by_id(session=session, user_id=user.user_id)
    unit = get_unit_by_id(session=session, unit_id=details.unit_progress)

    # the user is doing a unit they've already done
    if user.unit_progress >= details.unit_progress:
        return False

    # if they're on their current unit, update their progress
    if details.lesson_index >= unit.lesson_count:
        user.unit_progress += 1
        user.lesson_index = 0
    elif details.lesson_index > user.lesson_index:
        user.lesson_index = details.lesson_index
    else:
        return False

    session.add(user)
    session.commit()
    session.refresh(user)

    return True


def get_user_xp(session: Session, user: Users) -> XpResponse:
    """
    Get a user's total and daily xp
    """

    user = get_user_by_id(session=session, user_id=user.user_id)
    
    daily_xp_q = select(UserXP).where(UserXP.user_id == user.user_id).where(UserXP.day == date.today())
    daily_xp = session.exec(daily_xp_q).all()

    if daily_xp:
        daily_xp_amt = daily_xp[0].xp
    else:
        daily_xp_amt = 0

    total_xp_q = select(UserXP.xp).where(UserXP.user_id == user.user_id)
    total_xp = sum(session.exec(total_xp_q).all())

    return XpResponse(
        user_id=user.user_id,
        daily_xp=daily_xp_amt,
        total_xp=total_xp,
    )


def update_user_xp(session: Session, user: Users, amount: int) -> XpResponse:
    """
    Update a user's daily xp. Respond with the current daily xp total and all-time total
    """

    # make sure user exists
    user = get_user_by_id(session=session, user_id=user.user_id)

    daily_xp_q = select(UserXP).where(UserXP.user_id == user.user_id).where(UserXP.day == date.today())
    daily_xp = session.exec(daily_xp_q).all()

    if daily_xp:
        daily_xp[0].xp += amount
        amount = daily_xp[0].xp
        session.add(daily_xp[0])
        session.commit()
        session.refresh(daily_xp[0])
    else:
        user.days_logged += 1
        todays_xp = UserXP(
            user_id=user.user_id,
            xp=amount,
        )
        session.add(user)
        session.add(todays_xp)
        session.commit()
        session.refresh(user)


    total_xp_q = select(UserXP.xp).where(UserXP.user_id == user.user_id)
    total_xp = sum(session.exec(total_xp_q).all())

    return XpResponse(
        user_id=user.user_id,
        daily_xp=amount,
        total_xp=total_xp,
    )


def get_xp_dates(session: Session, user: Users, amt: int) -> list[date]:
    """
    Get a specified number of the most recent days a user's xp has changed
    """

    date_q = select(UserXP.day).where(UserXP.user_id == user.user_id).order_by(UserXP.day.desc()).limit(amt)
    dates = session.exec(date_q).all()

    return dates




##                 ##
##      Units      ##
##                 ##

def get_units(session: Session, lower: int = 0, upper: Optional[int] = None) -> List[Units]:
    """
    Get an ascending list of units with unit ids in a specified range

    :param lower: An inclusive lower bound on unit ids of returned units
    :param upper: An inclusive upper bound on unit ids of returned units. If None, all units are returned
    :return: An list of units
    """

    total_units = session.exec(select(func.count(Units.unit_id))).first()
    limit_range = range(lower, total_units+1) if (upper is None) else range(lower, upper+1)

    get_units = select(Units).where(Units.unit_id.in_(limit_range))
    units = session.exec(get_units).all()
    updated_units = count_lessons(session=session, units=units)

    return updated_units


def get_unit_by_id(session: Session, unit_id: int) -> Units:
    """
    Gets an individual unit by id

    :param unit_id: The id of the requested unit
    :return: The requested unit
    :raises EntityNotFouncException: No such unit exists for the given id
    """

    unit = session.get(Units, unit_id)
    if unit:
        return unit

    raise EntityNotFoundException(entity_name="Units", entity_id=unit_id)


def create_unit(session: Session, details: AddUnit) -> Units:
    """
    Add a new unit to the databse

    :param details: An AddUnit model contining a unit title and description
    :return:
    """

    unit = Units(
        **details.model_dump()
    )

    session.add(unit)
    session.commit()
    session.refresh(unit)

    return unit


def delete_unit(session: Session, unit_id: int) -> Units:
    """
    Delete a unit from the database

    :param unit_id: The id of th eunit to delete
    """

    unit = get_unit_by_id(session=session, unit_id=unit_id)

    query = select(LessonsInUnit).where(LessonsInUnit.unit_id == unit_id)
    unit_lessons = session.exec(query).all()

    for ul in unit_lessons:
        session.delete(ul)

    session.delete(unit)
    session.commit()

    return unit


def add_lesson_to_unit(session: Session, details: UpdateLessonInUnit) -> LessonsInUnit:
    """
    Add a lesson to a unit
    """

    # make sure both the unit and lesson exist
    get_unit_by_id(session=session, unit_id=details.unit_id)
    get_lesson_by_id(session=session, lesson_id=details.lesson_id)

    # make sure the mapping does not already exist
    relationship_query = select(func.count(LessonsInUnit.unit_id)) \
    .where(LessonsInUnit.unit_id == details.unit_id) \
    .where(LessonsInUnit.lesson_index == details.lesson_index)

    lesson_in_unit = session.exec(relationship_query).one()
    if lesson_in_unit:
        raise DuplicateEntitiyException(entity_name="unit_lesson_index",
                                        entity_id=f'u_id: {details.unit_id}, ' +
                                        f'index: {details.lesson_index}')
    
    new_lesson_in_unit = LessonsInUnit(
        **details.model_dump()
    )

    session.add(new_lesson_in_unit)
    session.commit()
    session.refresh(new_lesson_in_unit)

    return new_lesson_in_unit


def remove_lesson_from_unit(session: Session, details: UpdateLessonInUnit) -> LessonsInUnit:
    """
    Remove a lesson from a unit
    """

    lesson_query = select(LessonsInUnit) \
    .where(LessonsInUnit.unit_id == details.unit_id) \
    .where(LessonsInUnit.lesson_index == details.lesson_index)

    lesson_in_unit = session.exec(lesson_query).all()

    print("QRESULT:", lesson_in_unit)

    if not lesson_in_unit:
        raise UnrelatedEntitiesException(first_name="Unit",
                                         first_id=details.unit_id,
                                         second_name="Index", 
                                         second_id=f'{details.lesson_index}')

    session.delete(lesson_in_unit[0])
    session.commit()

    return lesson_in_unit[0] 



##                   ##
##      Lessons      ##
##                   ##

def get_lessons_in_unit(session: Session, unit_id: int) -> List[Lessons]:
    """
    Gets a list of all Lessons associated with a given unit

    :param unit_id: The id of the unit containing the lessons
    :return: A list of lessons
    """

    get_related_lessons = select(LessonsInUnit).where(LessonsInUnit.unit_id == unit_id).order_by(LessonsInUnit.lesson_index)
    related_lessons = sorted(session.exec(get_related_lessons).all(), key=lambda relation: relation.lesson_index)
    sorted_ids = [lesson.lesson_id for lesson in related_lessons]

    get_lessons = select(Lessons).where(Lessons.lesson_id.in_(sorted_ids))
    lessons = session.exec(get_lessons).all() # not guaranteed to return lessons in the same order

    lesson_map = {lesson.lesson_id: lesson for lesson in lessons}
    lessons_by_index = [ lesson_map[_id] for _id in sorted_ids ]    

    updated_lessons = count_questions(session=session, lessons=lessons_by_index)

    return updated_lessons


def get_lesson_from_unit(session: Session, unit_id: int, lesson_id: int) -> Lessons:
    """
    Gets a lesson from a specified unit by lesson id

    :param unit_id: The id of the unit to get the lesson from
    :param lesson_id: The id of the requested lesson
    :return: The lesson corresponding to the provided lesson id
    :raises UnrelatedEntitiesException: Requested lesson does not exist in provided unit
    """

    lessons_in_unit = get_lessons_in_unit(session=session, unit_id=unit_id)
    lesson_ids = [lesson.lesson_id 
                  for lesson in lessons_in_unit]

    if lesson_id in lesson_ids:
        return lessons_in_unit[lesson_ids.index(lesson_id)]
    
    raise UnrelatedEntitiesException(first_name="Units", first_id=unit_id,
                                     second_name="Lessons", second_id=lesson_id)


def get_lesson_by_id(session: Session, lesson_id: int) -> Lessons:
    """
    Gets an individual lesson by lesson id

    :param lesson_id: The id of the requested lesson
    :return: The requested lesson
    :raises EntityNotFouncException: No such lesson exists for the given id
    """

    lesson = session.get(Lessons, lesson_id)
    if lesson:
        return lesson

    raise EntityNotFoundException(entity_name="Lessons", entity_id=lesson_id)


def create_lesson(session: Session, details: AddLesson) -> Lessons:
    """
    Add a new lesson to the database

    :param details: An AddLesson model contining a lesson title and type
    :return:
    """

    lesson = Lessons(
        **details.model_dump()
    )

    session.add(lesson)
    session.commit()
    session.refresh(lesson)

    return lesson


def delete_lesson(session: Session, lesson_id: int) -> Lessons:
    """
    Delete a lesson from the database

    :param lesson_id: The id of the lesson to delete
    """
    
    lesson = get_lesson_by_id(session=session, lesson_id=lesson_id)

    # remove all questions from the lesson
    for link_table in question_tables.values():        
        query = select(link_table).where(link_table.lesson_id == lesson_id)
        lesson_questions = session.exec(query).all()

        for lq in lesson_questions:
            session.delete(lq)

    session.delete(lesson)
    session.commit()

    return lesson


def add_question_to_lesson(session: Session, details: UpdateQuestionInLesson) -> QuestionInLessonModel:
    """
    Add an existing question to an existing lesson

    :param details: 
    :returns:
    :raises DuplicateEntitiyException:
    """

    link_table = _get_link_table(details.question_type)

    # check that both the lesson and question exist
    get_lesson_by_id(session=session, lesson_id=details.lesson_id)
    get_question(session=session, question_type=details.question_type, question_id=details.question_id)

    # check that the current pairing does not already exist
    relationship_query = select(func.count(link_table.question_id)) \
    .where(link_table.lesson_id == details.lesson_id) \
    .where(link_table.question_id == details.question_id)

    question_in_lesson = session.exec(relationship_query).one()
    if question_in_lesson:
        raise DuplicateEntitiyException(entity_name=details.question_type.name,
                                        entity_id=f'l_id: {details.lesson_id}, q_id: {details.question_id}')

    new_question_in_lesson = link_table(
        **details.model_dump()
    )

    session.add(new_question_in_lesson)
    session.commit()
    session.refresh(new_question_in_lesson)

    return QuestionInLessonModel(**details.model_dump())


def remove_question_from_lesson(session: Session, details: UpdateQuestionInLesson) -> QuestionInLessonModel:
    """
    Remove a question from a lesson

    :param details:
    :returns:
    :raises UnrelatedEntitiesException: The specified question is not in the lesson
    """

    link_table = _get_link_table(details.question_type)

    question_query = select(link_table) \
    .where(link_table.lesson_id == details.lesson_id) \
    .where(link_table.question_id == details.question_id)

    question_in_lesson = session.exec(question_query).all()
    if not question_in_lesson: 
        raise UnrelatedEntitiesException(first_name="Lesson", 
                                         first_id=details.lesson_id,
                                         second_name=f'{details.question_type.name} Question', 
                                         second_id=details.question_id)

    session.delete(question_in_lesson[0])
    session.commit()

    return QuestionInLessonModel(**details.model_dump()) 


def count_lessons(session: Session, units: list[Units]) -> list[Units]:
    """
    Updates the count of the number of lessons in each unit in a list of units. 

    FIXME   This could probably be sped up by grouping the units by id and only counting once,
            but it works well enough for now 
    
    :param units: The list of units to be updated
    :return: The updated units
    """

    for unit in units:
        lesson_count = session.exec(
            select(func.count(LessonsInUnit.unit_id)).where(LessonsInUnit.unit_id == unit.unit_id)
        ).first()
        unit.lesson_count = lesson_count
        session.add(unit)

    session.commit()
    return units


def _get_link_table(question_type: QuestionType) -> SQLModel:
    """
    Get the reationship table between a lesson and a question type
    """
    
    match question_type:
        case QuestionType.CAMERA:
            return CameraQuestionsInLesson
        case QuestionType.MULTIPLE_CHOICE:
            return MultipleChoiceQuestionsInLesson
        case QuestionType.MATCHING:
            return MatchingQuestionsInLesson
        case QuestionType.FILL_IN_THE_BLANK:
            return FillInTheBlankQuestionsInLesson
        case QuestionType.WATCH_TO_LEARN:
            return WatchToLearnQuestionsInLesson



##                     ##
##      Questions      ##
##                     ##

def get_questions_in_lesson(session: Session, lesson_id: int) -> List[SQLModel]:
    """
    Get all questions used by a lesson regardless of question type
    
    :param lesson_id: The lesson to get the questions of 
    :return: A list of questions contained in the lesson
    """
    global question_tables

    all_questions = []

    for q_table, link_table in question_tables.items():
        get_related_questions = select(link_table.question_id).where(link_table.lesson_id == lesson_id)
        question_ids = session.exec(get_related_questions).all()

        get_questions = select(q_table).where(q_table.question_id.in_(question_ids))
        all_questions += session.exec(get_questions).all()

    return all_questions


def get_question(session: Session, question_type: QuestionType, question_id: int) -> SQLModel:
    """
    Gets the answer of a question by question type and id

    :param question_type: The type of question to search for: [Multiple Choice, Matching, Fill in the Blank]
    :param question_id: The id of the question 
    :return: The question's answer
    :raises InvalidRequestException: The requested question type does not support an "answer" field
    :raises EntityNotFoundException: A question with the provided id does not exist in the provided type table
    """

    search_table = None

    match question_type:
        case QuestionType.CAMERA:
            search_table = CameraQuestions
        case QuestionType.MULTIPLE_CHOICE:
            search_table = MultipleChoiceQuestions
        case QuestionType.MATCHING:
            search_table = MatchingQuestions
        case QuestionType.FILL_IN_THE_BLANK:
            search_table = FillInTheBlankQuestions
        case QuestionType.WATCH_TO_LEARN:
            search_table = WatchToLearnQuestions
        case _:
            raise InvalidRequestExcpetion(entity_name="Question Type", 
                                          msg=f"Question Type [{question_type}] is unsupported for this route")

    
    question = session.get(search_table, question_id)

    if question:
        return question
    
    raise EntityNotFoundException(entity_name=question_type.name, entity_id=question_id)
 

def get_questions_by_sign(session: Session, question_type: QuestionType, sign: str) -> List[SQLModel]:
    """
    Get a list of questions by type based on their answers
    
    """

    search_table = None
    _filter = None

    match question_type:
        case QuestionType.CAMERA:
            search_table = CameraQuestions
            _filter = CameraQuestions.sign == sign
        case QuestionType.MULTIPLE_CHOICE:
            search_table = MultipleChoiceQuestions
            _filter = MultipleChoiceQuestions.answer == sign
        case QuestionType.FILL_IN_THE_BLANK:
            search_table = FillInTheBlankQuestions
            _filter = FillInTheBlankQuestions.answer == sign
        case QuestionType.WATCH_TO_LEARN:
            search_table = WatchToLearnQuestions
            _filter = WatchToLearnQuestions.sign == sign
        case _:
            raise InvalidRequestExcpetion(entity_name="Question Type", 
                                          msg=f"Question Type [{question_type}] is unsupported for this route")

    
    question_query = select(search_table).where(_filter)
    questions = session.exec(question_query).all()

    return questions


def add_watch_question(session: Session, details: AddWatchQuestion) -> WatchToLearnQuestions:
    """
    Add a new WatchToLearn question to the database

    """

    # check that signs exist
    _check_signs(
        session=session, 
        signs=[details.sign, details.starting_position]
    )

    new_q = WatchToLearnQuestions(
        text=details.text,
        sign=details.sign,
        starting_position=details.starting_position,
        num_hands=details.num_hands,
        motion=details.motion
    )
    session.add(new_q)
    session.commit()
    session.refresh(new_q)

    return new_q


def add_camera_question(session: Session, details: AddCameraQuestion) -> CameraQuestions:
    """
    Add a new SignToCamera question to the database
    
    """
    
    _check_signs(
        session=session, 
        signs=[details.sign, details.starting_position]
    )

    new_q = CameraQuestions(
        text=details.text,
        sign=details.sign,
        starting_position=details.starting_position,
        num_hands=details.num_hands,
        motion=details.motion
    )
    session.add(new_q)
    session.commit()
    session.refresh(new_q)

    return new_q


def add_mc_question(session: Session, details: AddMultipleChoicQuestion) -> MultipleChoiceQuestions:
    """
    Add a new MultipleChoice question to the database
    
    """

    _check_signs(
        session=session, 
        signs=(details.options + [details.answer])
    )

    new_q = MultipleChoiceQuestions(
        text=details.text,
        option_1=details.options[0],
        option_2=details.options[1],
        option_3=details.options[2],
        option_4=details.options[3],
        answer=details.answer
    )
    session.add(new_q)
    session.commit()
    session.refresh(new_q)

    return new_q


def add_fill_question(session: Session, details: AddFillInTheBlankQuestion) -> FillInTheBlankQuestions:
    """
    Add a new FillInTheBlank question to the database
    
    """

    _check_signs(
        session=session, 
        signs=[details.answer]
    )
        
    new_q = FillInTheBlankQuestions(
        text=details.text,
        image_path=details.image_path,
        answer=details.answer
    )

    session.add(new_q)
    session.commit()
    session.refresh(new_q)

    return new_q


def add_matching_question(session: Session, details: AddMatchingQuestion) -> MatchingQuestions:
    """
    Add a new Matching question to the database
    
    """

    new_q = MatchingQuestions(
        text=details.text,
        pairs=details.pairs
    )

    session.add(new_q)
    session.commit()
    session.refresh(new_q)

    return new_q


def delete_question(session: Session, question_type: QuestionType, question_id: int) -> SQLModel:
    """
    Delete a question of a given type by question id
    
    """

    table, link_table = None, None

    match question_type:
        case QuestionType.CAMERA:
            table = CameraQuestions
            link_table = CameraQuestionsInLesson
        case QuestionType.MULTIPLE_CHOICE:
            table = MultipleChoiceQuestions
            link_table = MultipleChoiceQuestionsInLesson
        case QuestionType.MATCHING:
            table = MatchingQuestions
            link_table = MatchingQuestionsInLesson
        case QuestionType.FILL_IN_THE_BLANK:
            table = FillInTheBlankQuestions
            link_table = FillInTheBlankQuestionsInLesson
        case QuestionType.WATCH_TO_LEARN:
            table = WatchToLearnQuestions
            link_table = WatchToLearnQuestionsInLesson

    link_query = select(link_table).where(link_table.question_id == question_id)
    questions_in_lesson = session.exec(link_query).all()

    # remove each foreign key referencing the question
    # No on-delete cascade will be the death of me...
    for linked_question in questions_in_lesson:
        session.delete(linked_question)
    session.commit()   

    question = session.get(table, question_id)

    if question:
        session.delete(question)
        session.commit()
        return question

    raise EntityNotFoundException(entity_name=question_type.name, entity_id=question_id)


def count_questions(session: Session, lessons: list[Lessons]) -> None:
    """
    Updates the count of the number of questions in each lesson in a list of lessons. 

    :param lessons: The list of lessons to be updated
    :return: The updated list of lessons
    """
    global question_tables

    for lesson in lessons:
        question_count = 0
        for link_table in question_tables.values(): 
            question_count += session.exec(
                    select(
                        func.count(link_table.lesson_id)
                    ).where(link_table.lesson_id == lesson.lesson_id)
                ).first()
           
        lesson.question_count = question_count
        session.add(lesson)

    session.commit()
    return lessons


def ans_encode(data: str):
    """
    Encodes a given string into a non human-readable string of integers.

    :IMPORTANT: This encoding is not a secure hash and should not be used to encrypt any 
    sensitive data. It just makes a string pretty hard to read unless you really try.
    
    :param data: A string to encode
    :return: An encoded version of the string
    """

    encoded_string = [
        f"{ord(c) * 49}-" if (ord(c) % 2) else f"{ord(c) * 98}-" 
        for c in data
        ]

    return "".join(encoded_string)[:-1]


def ans_decode(data: str):
    """
    Decodes a given string of data encoded with the ans_encode function.

    :param data: An 'ans_encode' encoded string
    :return: A decoded string
    """

    decoded_chars = [
        chr(int(c) // 49) if (int(c) % 2) else chr(int(c) // 98) 
        for c in data.split('-')
        ]

    return "".join(decoded_chars)



##                     ##
##        Signs        ##
##                     ##

def get_sign(session: Session, sign: str) -> Signs:
    """
    Retrieve a sign from the database
    """

    sign_ = session.get(Signs, sign)
    if sign_:
        return sign_
    
    raise EntityNotFoundException(entity_name="Signs", entity_id=sign)


def create_sign(session: Session, new_sign: CreateSign) -> Signs:
    """
    Create a new sign and add it to the database
    """
    
    sign = session.get(Signs, new_sign.sign)
    if sign:
        raise DuplicateEntitiyException

    sign = Signs(**new_sign.model_dump())
    session.add(sign)
    session.commit()
    session.refresh(sign)
    return sign


def update_sign(session: Session, details: UpdateSign) -> Signs:
    """
    Update the image path of a sign
    """

    sign = get_sign(session=session, sign=details.sign_key)

    sign.image_path = details.image_path
    session.add(sign)
    session.commit()
    session.refresh(sign)

    return sign


def delete_sign(session: Session, sign: str) -> Signs:
    """
    TODO Fix :)

    Delete a sign from the database
    """

    sign = get_sign(session=session, sign=sign)
    session.delete(sign)
    session.commit()

    return sign


def _check_signs(session: Session, signs: List[str]) -> bool:
    """
    Check if all signs in a list are present in the db
    """

    for sign in signs:
        _sign = session.get(Signs, sign)
        if not _sign:
            raise EntityNotFoundException(
            entity_name="Signs",
            entity_id=sign
        )
        
