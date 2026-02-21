from fastapi import Request

def flash_msg(request,message,category):
    request.session["flash"] = {
        "message": message,
        "category": category
    }

def get_flash(request: Request):
    return request.session.pop("flash", None)