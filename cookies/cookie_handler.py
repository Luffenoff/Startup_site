from flask import request, make_response

class CookieHandler:
    @staticmethod
    def set_cookie(response, key, value, max_age=None):
        response.set_cookie(key, value, max_age=max_age, httponly=True)
        return response

    @staticmethod
    def get_cookie(key):
        return request.cookies.get(key)

    @staticmethod
    def delete_cookie(response, key):
        response.delete_cookie(key)
        return response
