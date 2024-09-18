# add admin routes here.
# This is my rank 3 feature so please don't work here ~or~ 
# please first let me know if something here needs to change 
# thanks! - charlie

from fastapi import APIRouter, Depends
from sqlmodel import Session

from signable import database as db
from signable.routers.users_router import get_current_user

from signable.entities.database_entities import QuestionType, Users
from signable.entities.lesson_entities import (
    AddCameraQuestion,
    AddFillInTheBlankQuestion,
    AddLesson,
    AddMatchingQuestion,
    AddMultipleChoicQuestion,
    AddUnit,
    AddWatchQuestion,
    CameraQuestionResponse,
    CreateSign,
    FillInTheBlankQuestionResponse,
    LessonInUnitModel,
    LessonInUnitResponse,
    LessonModel,
    LessonResponse,
    MatchingQuestionResponse,
    MultipleChoiceQuestionResponse,
    QuestionCollection,
    QuestionInLessonResponse,
    QuestionResponse, 
    SignResponse,
    UnitModel,
    UnitResponse,
    UpdateLessonInUnit,
    UpdateQuestionInLesson,
    UpdateSign,
    WatchToLearnQuestionResponse,
)


admin_router = APIRouter(prefix="/admin", tags=["Admin"])


def _check_is_admin(user: Users) -> None:
    """
    Check user permissions
    """

    if not user.is_admin:
        raise db.PermissionsException()


@admin_router.get(path="/sign/{sign}", response_model=SignResponse)
def get_sign(sign: str, user: Users = Depends(get_current_user), 
             session: Session = Depends(db.get_session)) -> SignResponse:
    """
    Retrieve a provided sign

    :param sign: The sign to retreieve
    :return: A SignResponse containing the specified sign
    """
    
    _check_is_admin(user=user)

    return SignResponse(
        msg="retrieved sign",
        sign=db.get_sign(session=session, sign=sign)
    )


@admin_router.post(path="/sign/", response_model=SignResponse)
def add_sign(new_sign: CreateSign, user: Users = Depends(get_current_user), 
             session: Session = Depends(db.get_session)) -> SignResponse:
    """
    Create a new sign

    :param new_sign: The identifier of sign to be created \n
    :return: A SignResonse containing the created sign
    """
    _check_is_admin(user=user)

    return SignResponse(
        msg="created sign",
        sign=db.create_sign(session=session, new_sign=new_sign)
    )


@admin_router.put(path="/sign/", response_model=SignResponse)
def update_sign(details: UpdateSign, user: Users = Depends(get_current_user),
                session: Session = Depends(db.get_session)) -> SignResponse:
    """
    Update the image path of a given sign

    :param sign_key: The sign to update the image path for
    :param image_path: The new image path
    :return: A sign response containing the sign and it's updated path
    """
    _check_is_admin(user=user)

    return SignResponse(
        msg="updated sign",
        sign=db.update_sign(session=session, details=details)
    )


@admin_router.get(path="/question/{question_type}/{sign}", response_model=QuestionCollection)
def get_questions_by_answer(question_type: QuestionType, sign: str, 
                            user: Users = Depends(get_current_user),
                            session: Session = Depends(db.get_session)) -> QuestionCollection:
    """
    Get a list of questions by type based on the sign they use as their answer
    
    :note: MatchingQuestions are currently unsupported \n
    :param question_type: The type of question to search through \n
    :param sign: The sign used as an answer by those questions \n
    :return: A QuestionCollection containing all questions with the given sign as an answer
    """

    _check_is_admin(user=user)

    
    questions = db.get_questions_by_sign(session=session, question_type=question_type, sign=sign)
    match question_type:
        case QuestionType.CAMERA:
            question_responses = [CameraQuestionResponse(
                question_id=q.question_id,
                text=q.text,
                question_type=q.question_type,
                sign=q.sign,
                starting_position=q.starting_position,
                num_hands=q.num_hands,
                motion=q.motion
            ) for q in questions]
        case QuestionType.MULTIPLE_CHOICE:
            question_responses = [MultipleChoiceQuestionResponse(
                question_id=q.question_id,
                text=q.text,
                question_type=q.question_type,
                options=[q.option_1, q.option_2, q.option_3, q.option_4]
            ) for q in questions]
        case QuestionType.FILL_IN_THE_BLANK:
            question_responses = [FillInTheBlankQuestionResponse(
                question_id=q.question_id,
                text=q.text,
                question_type=q.question_type,
                image_path=db.ans_encode(q.image_path)
            ) for q in questions]
        case QuestionType.WATCH_TO_LEARN:
            question_responses = [ WatchToLearnQuestionResponse(
                question_id=q.question_id,
                text=q.text,
                question_type=q.question_type,
                sign=q.sign,
                starting_position=q.starting_position,
                num_hands=q.num_hands,
                motion=q.motion
            ) for q in questions]
        case _:
            raise db.InvalidRequestExcpetion(entity_name="Question Type", 
                                          msg=f"Question Type [{question_type}] is unsupported for this route")

    meta = {"count": len(question_responses)}

    return QuestionCollection(meta=meta, questions=question_responses)


@admin_router.post(path="/question/watch/", response_model=WatchToLearnQuestionResponse)
def create_watch_question(details: AddWatchQuestion,
                          user: Users = Depends(get_current_user), session: Session = Depends(db.get_session)) -> WatchToLearnQuestionResponse:

    """
    Create a new WatchToLearn question

    :return: A WatchToLearnQuestionResponse contining the details of the newly added questio
    """

    _check_is_admin(user=user)


    new_q = db.add_watch_question(session=session, details=details)
    return WatchToLearnQuestionResponse(
        **new_q.model_dump(), 
    )


@admin_router.post(path="/question/camera/", response_model=CameraQuestionResponse)
def create_camera_question(details: AddCameraQuestion,
                           user: Users = Depends(get_current_user), session: Session = Depends(db.get_session)) -> CameraQuestionResponse:
    """
    Create a new SignToCameraQuestion
    
    :return: a CameraQuestionResponse containing the details of the newly added question
    """

    _check_is_admin(user=user)


    new_q = db.add_camera_question(session=session, details=details)
    return CameraQuestionResponse(
        **new_q.model_dump(),
    )


@admin_router.post(path="/question/mc/", response_model=MultipleChoiceQuestionResponse)
def create_mc_question(details: AddMultipleChoicQuestion,
                           user: Users = Depends(get_current_user), session: Session = Depends(db.get_session)) -> MultipleChoiceQuestionResponse:
    """
    Create a new MultipleChoiceQuestion. Multiple choice questions have exatly 4 options
    
    :return: a MultipleChoiceQuestionResponse containing the details of the newly added question
    """
    
    _check_is_admin(user=user)

    new_q = db.add_mc_question(session=session, details=details)
    return MultipleChoiceQuestionResponse(
        **details.model_dump(),
        question_type=new_q.question_type,
        question_id=new_q.question_id,
    )



@admin_router.post(path="/question/fill/", response_model=FillInTheBlankQuestionResponse)
def create_fill_question(details: AddFillInTheBlankQuestion,
                           user: Users = Depends(get_current_user), session: Session = Depends(db.get_session)) -> FillInTheBlankQuestionResponse:
    """
    Create a new FillInTheBlankQuestion
    
    :return: a FillInTheBlankQuestionResponse containing the details of the newly added question
    """

    _check_is_admin(user=user)


    new_q = db.add_fill_question(session=session, details=details)
    return FillInTheBlankQuestionResponse(
        **new_q.model_dump(),
    )


@admin_router.post(path="/question/match/", response_model=MatchingQuestionResponse)
def create_match_question(details: AddMatchingQuestion,
                           user: Users = Depends(get_current_user), session: Session = Depends(db.get_session)) -> MatchingQuestionResponse:
    """
    Create a new MatchingQuesiton. Matching pairs are of the form ".A.B.C.D." etc. \n
    Each item seperted by . represents one pair.
    
    :return: a MatchingQuesitonResponse containing the details of the newly added question
    """
    
    _check_is_admin(user=user)


    new_q = db.add_matching_question(session=session, details=details)
    options = list(filter(None, details.pairs.split(".")))
    return MatchingQuestionResponse(
        **new_q.model_dump(),
        image_options=[db.ans_encode(o) for o in options],
        text_options=options,
    )


@admin_router.delete(path="/question/{question_type}/{question_id}", response_model=QuestionResponse)
def delete_question(question_type: QuestionType, question_id: int, 
                    user: Users = Depends(get_current_user), session: Session = Depends(db.get_session)) -> QuestionResponse:
    """
    Deletes a question of a given type by question id
    
    :return: The generic information of the deleted question
    """

    _check_is_admin(user=user)


    del_q = db.delete_question(session=session, question_type=question_type, question_id=question_id)
    return QuestionResponse(
        question_id=question_id,
        question_type=question_type,
        text=del_q.text,
    )


@admin_router.post(path="/lesson/", response_model=LessonResponse)
def create_lesson(details: AddLesson, user: Users = Depends(get_current_user), 
                  session: Session = Depends(db.get_session)) -> LessonResponse:
    """
    Create a new lesson

    :return: A LessonResponse containing the details of the newly created lesson
    """
    
    _check_is_admin(user=user)


    new_lesson = db.create_lesson(session=session, details=details)
    lesson = LessonModel(
        **new_lesson.model_dump(),
    )

    return LessonResponse(lesson=lesson)


@admin_router.delete(path="/lesson/{lesson_id}", response_model=LessonResponse)
def delete_lesson(lesson_id: int, user: Users = Depends(get_current_user), 
                  session: Session = Depends(db.get_session)) -> LessonResponse:
    """
    Delete a lesson by lesson id

    :return: A LessonResponse containing the details of the deleted lesson
    """

    _check_is_admin(user=user)


    deleted_lesson = db.delete_lesson(session=session, lesson_id=lesson_id)
    response = LessonModel(
        **deleted_lesson.model_dump(),
    )

    return LessonResponse(lesson=response)


@admin_router.put(path="/lesson/question/", response_model=QuestionInLessonResponse)
def add_question_to_lesson(details: UpdateQuestionInLesson, user: Users = Depends(get_current_user),
                           session: Session = Depends(db.get_session)) -> QuestionInLessonResponse:
    """
    Add a new question to an existing lesson

    :return: The ids of the newly associated question and lesson
    """
    
    _check_is_admin(user=user)

    return QuestionInLessonResponse(
        msg="added question",
        details=db.add_question_to_lesson(
            session=session, 
            details=details
        )
    )


@admin_router.delete(path="/lesson/question/", response_model=QuestionInLessonResponse)
def remove_question_from_lesson(details: UpdateQuestionInLesson, user: Users = Depends(get_current_user),
                                session: Session = Depends(db.get_session)) -> QuestionInLessonResponse:
    """
    Remove a question fram a lesson

    :return: The ids of the removed question and lesson
    """

    _check_is_admin(user=user)
    
    return QuestionInLessonResponse(
        msg="removed question",
        details=db.remove_question_from_lesson(
            session=session, 
            details=details
        )
    )


@admin_router.post(path="/unit/", response_model=UnitResponse)
def create_unit(details: AddUnit, user: Users = Depends(get_current_user),
                 session: Session = Depends(db.get_session)) -> UnitResponse:
    """
    Create a new unit

    :return: A UnitResopnse containing the details of the newly created unit
    """

    _check_is_admin(user=user)


    new_unit = db.create_unit(session=session, details=details)

    unit = UnitModel(
        **new_unit.model_dump(),
    )

    return UnitResponse(unit=unit)


@admin_router.delete(path="/unit/", response_model=UnitResponse)
def delete_unit(unit_id: int, user: Users = Depends(get_current_user), 
                session: Session = Depends(db.get_session)) -> UnitResponse:
    """
    Delete a unit by unit id

    """
    
    _check_is_admin(user=user)


    deleted_unit = db.delete_unit(session=session, unit_id=unit_id)
    response = UnitModel(
        **deleted_unit.model_dump()
    )

    return UnitResponse(unit=response)


@admin_router.put(path="/unit/lesson/", response_model=LessonInUnitResponse)
def add_lesson_to_unit(details: UpdateLessonInUnit, user: Users = Depends(get_current_user),
                       session: Session = Depends(db.get_session)) -> LessonInUnitResponse:
    """
    Add a lesson to a unit

    :return: The ids of the newly associated lesson and unit, along with the index of the lesson in the unit
    """

    _check_is_admin(user=user)

    new_lesson_in_unit = db.add_lesson_to_unit(session=session, details=details)
    return LessonInUnitResponse(
        msg="added lesson",
        details=LessonInUnitModel(**new_lesson_in_unit.model_dump())
    )


@admin_router.delete(path="/unit/lesson/", response_model=LessonInUnitResponse)
def remove_question_from_lesson(details: UpdateLessonInUnit, user: Users = Depends(get_current_user),
                       session: Session = Depends(db.get_session)) -> LessonInUnitResponse:
    """
    Remove a lesson from a unit

    :return: The ids of the removed lesson and unit in the association, along with the index of the lesson in the unit
    """

    _check_is_admin(user=user)

    removed_lesson = db.remove_lesson_from_unit(session=session, details=details)
    return LessonInUnitResponse(
        msg="removed Lesson",
        details=LessonInUnitModel(**removed_lesson.model_dump()),
    )

