from sqlalchemy import func

from Resources import db, app
from Resources.models import *


def getUserbyName(
        userName: str
        ):
    """Returns user record from database, search by UserName

    Arguments:
        :userName: -- Username to check

    Returns:
        User record or 404 error
    """
    with app.app_context():
        return db.one_or_404(db.select(Users).filter_by(Username=userName))

def getUserbyID(
        userID: str
        ):
    """Returns user record from database, search by ID

    Arguments:
        :userID: -- User ID to check

    Returns:
        User record or 404 error
    """
    with app.app_context():
        return db.one_or_404(db.select(Users).filter_by(ID=userID))

def getUserSetting(
        userID: str,
        setting: str #TODO: Change to enum
        ):
    """Returns chosen setting for specified user ID from database

    Arguments:
        :userID: -- User ID to check
        :setting: -- User setting to get

    Returns:
        User record or 404 error
    """
    with app.app_context():
        return db.one_or_404(
                    db.session.query(UserSettings).\
                        filter_by(
                            Setting=setting,
                            UserID=userID)
                    )

# TODO: Abstract so only one range fucntion can be used
def getTimeRangeMonth(
        table: Table,
        userID: str        
    ) -> RangeMonth:
    """Returns month range for user data in specified table

    Arguments:
        :table: -- Table for which datarange is requested
        :userID: -- UserID

    Returns:
        RangeMonth object with beginning and end dates. Both None if data is not
        present for specified user.
    """
    
    with app.app_context():
        # NICE-TO-HAVE: Refactor query if possible or abstract as function  
        beginning = db.session.query(table.columns.Month).\
                                order_by(table.columns.Month.asc()).\
                                        filter_by(UserID=userID).first()[0]
        end =       db.session.query(table.columns.Month).\
                                order_by(table.columns.Month.desc()).\
                                        filter_by(UserID=userID).first()[0]
        return RangeMonth(
                    beginning = beginning if beginning else None,
                    end = end if end else None
                    )

def getTimeRangeDate(
        table: Table,
        userID: str        
    ) -> RangeDate:
    """Returns date range for user data in specified table

    Arguments:
        :table: -- Table for which datarange is requested
        :userID: -- UserID

    Returns:
        RangeDate object with beginning and end dates. Both None if data is not
        present for specified user.
    """
    
    with app.app_context():
        # NICE-TO-HAVE: Refactor query if possible or abstract as function
        beginning = db.session.query(table.columns.DateTime).\
                                order_by(table.columns.DateTime.asc()).\
                                        filter_by(UserID=userID).first()[0]
        end =       db.session.query(table.columns.DateTime).\
                                order_by(table.columns.DateTime.desc()).\
                                        filter_by(UserID=userID).first()[0]
        return RangeDate(
                    beginning = beginning if beginning else None,
                    end = end if end else None
                    )

def getsummaryByTypeGrouped(
        table: Table,
        userID: str,
        range: RangeMonth
    ) -> list:
    """Returns IncomeSummary for specified user in specified timeframe

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID
        :range: -- Timeframe for which data to provide

    Returns:
        List containing summary of income by type in specified timeframe
    """
    
    with app.app_context():
        # NICE-TO-HAVE: Refactor query if possible or abstract as function
        IncomeSummarydata = db.session.query(
                                        table.columns.Type,
                                         func.sum(table.columns.Amount)).\
                                filter_by(UserID=userID).\
                                filter(
                                    table.columns.Month>=range.beginning,
                                    table.columns.Month<=range.end).\
                                order_by(table.columns.Amount.desc()).\
                                group_by(table.columns.Type).\
                                all()
        return IncomeSummarydata

def getDataFromTableforUser(
        table: Table,
        userID: str
    ) -> list:
    """Returns data from specified table for specified user

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID

    Returns:
        Data from table
    """

    with app.app_context():
        data = db.session.query(table).filter_by(UserID=userID).all()
        return data

def getMonthlySummaryRange(
        table: Table,
        userID: str,
        range: RangeMonth
    ) -> list:
    """Returns any monthly summary table data for specified user in specified timeframe

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID
        :range: -- Timeframe for which data to provide

    Returns:
        List containing summary in specified timeframe
    """
    
    with app.app_context():
        summary = db.session.query(
                                table.columns.Month,
                                table.columns.Amount).\
                            filter_by(UserID=userID).\
                            filter(
                                table.columns.Month>=range.beginning,
                                table.columns.Month<=range.end).\
                            all()
        return summary

def getMonthlyTypeSummaryRange(
        table: Table,
        userID: str,
        range: RangeMonth
    ) -> list:
    """Returns any monthly summary type table data for specified user in specified timeframe

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID
        :range: -- Timeframe for which data to provide

    Returns:
        List containing summary of types in specified timeframe
    """
    
    with app.app_context():
        summary = db.session.query(
                                table.columns.Month,
                                table.columns.Amount,
                                table.columns.Type
                                ).\
                            filter_by(UserID=userID).\
                            filter(
                                table.columns.Month>=range.beginning,
                                table.columns.Month<=range.end).\
                            all()
        return summary