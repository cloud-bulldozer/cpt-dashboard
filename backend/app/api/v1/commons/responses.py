def response_200(example):
    return {
                "content": {
                    "application/json": {
                        "example": example,
                    }
                },
            }


def response_422():
    return {
                "content": {
                    "application/json": {
                        "example": {"error": "invalid date format, start_date must be less than end_date"},
                    }
                },
            }
