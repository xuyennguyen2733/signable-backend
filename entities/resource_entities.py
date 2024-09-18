from datetime import date, datetime

from pydantic import BaseModel
from sqlmodel import SQLModel

##                  ##
##      Models      ##
##                  ##

class Metadata(BaseModel):

    count: int

