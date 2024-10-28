import uuid
from .cookie_handler import CookieHandler

class SessionManager:
    @staticmethod
    def start_session(response, user_id):
        session_id = str(uuid.uuid4())
        response = CookieHandler.set_cookie(response, 'session_id', session_id, max_age=3600)
        return response

    @staticmethod
    def end_session(response):
        response = CookieHandler.delete_cookie(response, 'session_id')
        return response

    @staticmethod
    def get_user_id_from_session():
        session_id = CookieHandler.get_cookie('session_id')
        return session_id
