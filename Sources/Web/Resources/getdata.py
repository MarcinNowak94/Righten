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
        return db.one_or_404(db.session.query(Users).filter_by(ID=userID))

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

#TODO: use getSummaryByColumn add only grouping
def getSummaryByColumnGrouped(
        table: Table,
        userID: str,
        range: RangeMonth,
        column: str
    ) -> list:
    """Returns grouped summary by specified column for specified user in specified timeframe

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID
        :range: -- Timeframe for which data to provide
        :column: -- Column by wich data should be grouped

    Returns:
        List containing summary by column in specified timeframe
    """
    
    with app.app_context():
        return db.session.query(
                            table.columns[column],
                            func.sum(table.columns.Amount)).\
                        filter_by(UserID=userID).\
                        filter(
                            table.columns.Month>=range.beginning,
                            table.columns.Month<=range.end).\
                        order_by(table.columns.Amount.asc()).\
                        group_by(table.columns[column]).\
                        all()

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

def getDataSubsetFromTableforUser(
        table: Table,
        userID: str,
        column: str,
        list: list[str]
    ) -> list:
    """Returns data from specified table for specified user

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID
        :column: -- Column by wich tables differ
        :list: -- List of values for which data should be provided

    Returns:
        Data from table by column in specified timeframe for specified list 
    """

    with app.app_context():
        data = db.session.query(table).\
                            filter_by(UserID=userID).\
                            where(table.columns[column].in_(list)).\
                            all()
        return data

def getMonthRangeDataFromTableforUser(
        table: Table,
        userID: str,
        range: RangeMonth
    ) -> list:
    """Returns data from specified table for specified user and specified date range

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID
        :range: -- Timeframe for which data to provide

    Returns:
        Data in specified range from table
    """

    with app.app_context():
        data = db.session.query(table).\
                            filter_by(UserID=userID).\
                            filter(
                                table.columns.Month>=range.beginning,
                                table.columns.Month<=range.end).\
                            all()
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

def getMonthlySummaryByColumn(
        table: Table,
        userID: str,
        range: RangeMonth,
        column: str
    ) -> list:
    """Returns any monthly summary by column table data for specified user in specified timeframe

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID
        :range: -- Timeframe for which data to provide
        :column: -- Column by wich tables differ

    Returns:
        List containing summary by column in specified timeframe
    """
    
    with app.app_context():
        summary = db.session.query(
                                table.columns.Month,
                                table.columns.Amount,
                                table.columns[column]
                            ).\
                            filter_by(UserID=userID).\
                            filter(
                                table.columns.Month>=range.beginning,
                                table.columns.Month<=range.end).\
                            all()
        return summary

def getMonthlySummarySubsetByColumn(
        table: Table,
        userID: str,
        range: RangeMonth,
        column: str,
        list: list[str]
    ) -> list:
    """Returns any monthly summary by column table data for specified user in specified timeframe

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID
        :range: -- Timeframe for which data to provide
        :column: -- Column by wich tables differ
        :list: -- List of values for which data should be provided

    Returns:
        List containing summary by column in specified timeframe for specified list 
    """
    
    with app.app_context():
        summary = db.session.query(
                                table.columns.Month,
                                table.columns.Amount,
                                table.columns[column]
                            ).\
                            filter_by(UserID=userID).\
                            filter(
                                table.columns.Month>=range.beginning,
                                table.columns.Month<=range.end).\
                            where(table.columns[column].in_(list)).\
                            all()
        return summary

def getMonthlyTopExpenditures(
        table: Table,   #TODO: Accept only Top10ProductsMonthly and Top10ProductTypesMonthly
        userID: str,
        range: RangeMonth,
        column: str     #TODO: Base column on table
    ) -> list:
    """Returns monthly data for expenditures for top 10 products or types for specified user in specified timeframe

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID
        :range: -- Timeframe for which data to provide
        :column: -- Column by wich table differ

    Returns:
        List containing summary of expenditures for top 10 products or types
    """
    
    with app.app_context():
        summary = db.session.query(
                                table.columns.Month,
                                table.columns.Sum,  #TODO: Change to amount in database to unify data and merge with getMonthlySummaryByColumn()
                                table.columns[column]
                            ).\
                            filter_by(UserID=userID).\
                            filter(
                                table.columns.Month>=range.beginning,
                                table.columns.Month<=range.end).\
                            all()
        
        return summary

def getMonthlyBilanceSummaryforUser(
        table: Table,
        userID: str,
        range: RangeMonth
    ) -> list:
    """Returns data from specified table for specified user

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID        
        :range: -- Timeframe for which data to provide
        :column: -- Column by wich table differ

    Returns:
        Table data summary for table by specified column in specified range for specified user
    """

    with app.app_context():
        data = db.session.query(
                                db.func.round(db.func.sum(table.columns.Income)),
                                db.func.round(db.func.sum(table.columns.Expenditures)),
                                db.func.round(db.func.sum(table.columns.Bills))
                            ).\
                            filter_by(UserID=userID).\
                            filter(
                                table.columns.Month>=range.beginning,
                                table.columns.Month<=range.end).\
                            all()
        # Compatibility with createpiechartdataset
        summary = [
                ["Income", data[0][0]],
                ["Expenditures", data[0][1]],
                ["Bills", data[0][2]]
            ]
        return summary

def getTopNProductOrTypesforUser(
        table: Table,
        userID: str,
        column: str,     #TODO: Base column on table
        limit: int=0
    ) -> list:
    """Returns N records from specified summary table for specified user by specified column

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID
        :column: -- Column name to pick
        :limit: -- Return only specified amount of records

    Returns:
        List of specified data from table 
    """

    with app.app_context():
        data = db.session.query(table.columns[column],
                                  table.columns.Amount).\
                            filter_by(UserID=userID).\
                            order_by(table.columns.Times.desc()).\
                            limit(limit).\
                            all()
        return data

def getSpecifiedProductsOrTypesforUser(
        table: Table,
        userID: str,
        column: str,     #TODO: Base column on table
        list: list[str]
    ) -> list:
    """Returns data from specified summary table for specified user and specified column content

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID
        :column: -- Column name to pick
        :list: -- List of values for which data should be provided

    Returns:
        List of specified data from table
    """

    with app.app_context():
        data = db.session.query(table.columns[column],
                                  table.columns.Amount).\
                            filter_by(UserID=userID).\
                            order_by(table.columns.Times.desc()).\
                            where(table.columns[column].in_(list)).\
                            all()
        return data

def getMonthlyBilanceValueFor(
        table: Table,
        userID: str,
        range: RangeMonth,
        column: str
    ) -> list:
    """Returns specified column from MonthlySummary table  table data for specified user in specified timeframe

    Arguments:
        :table: -- Table for which data is requested
        :userID: -- UserID
        :range: -- Timeframe for which data to provide
        :column: -- Column by wich tables differ

    Returns:
        List containing summary by column (as Amount) in specified timeframe
    """
    
    with app.app_context():
        summary = db.session.query(
                                table.columns.Month,
                                table.columns[column].label("Amount")
                            ).\
                            filter_by(UserID=userID).\
                            filter(
                                table.columns.Month>=range.beginning,
                                table.columns.Month<=range.end).\
                            all()
        return summary
