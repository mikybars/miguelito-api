import json


def ok(body=None):
    if body is None:
        return response(200)
    else:
        return response(200, body.to_serializable())


def bad_request(msg, detail=None):
    return fail(400, msg, detail)


def forbidden():
    return response(403)


def server_error(msg, detail=None):
    return fail(500, msg, detail)


def fail(status_code, msg, detail=None):
    return response(status_code, {"message": msg, "detail": detail})


def response(status_code, body=None):
    result = {
        "headers": {
            "Access-Control-Allow-Origin": "*"
        },
        "statusCode": status_code
    }
    if body is not None:
        result['body'] = json.dumps(__new_dict_without_nones(body))

    return result


def __new_dict_without_nones(data):
    return {k: v for k, v in data.items() if v is not None}
