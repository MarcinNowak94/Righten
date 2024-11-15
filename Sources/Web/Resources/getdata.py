from Resources import db, app
from Resources.models import *

def getUser(
        checkeduser: str
        ):
    """Returns user record from database 

    Arguments:
        :checkeduser: -- User to check

    Returns:
        User record or 404 error
    """
    with app.app_context():
        return db.one_or_404(db.select(Users).filter_by(Username=checkeduser))