DEFAULT_COMPANY_URL = ""

class ResponseHandler:

    @classmethod
    def success(cls, message, status="accepted", code=200, data=None):
        return {
            "status": status,
            "message": message,
            "code": code,
            "data": data
        }

    @classmethod
    def error(cls, message, code=500):
        return {
            "status": "error",
            "error_reason": message,
            "code": code
        }

    @classmethod
    def not_found(cls, message, code=404):
        return {
            "status": "error",
            "error_reason": message,
            "code": code
        }

    @classmethod
    def unauthorized(cls, message, code=401):
        return {
            "status": "error",
            "error_reason": message,
            "code": code
        }

    @classmethod
    def credentials_required(cls, message, code=400):
        return {
            "status": "error",
            "error_reason": message,
            "code": code
        }