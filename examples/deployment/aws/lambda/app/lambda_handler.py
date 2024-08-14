from . import counter_app


def lambda_handler(event, context):
    count_up_to = int(event["body"]["number"])

    app = counter_app.application(count_up_to)
    action, result, state = app.run(halt_after=["result"])

    return {"statusCode": 200, "body": state.serialize()}


if __name__ == "__main__":
    print(lambda_handler({"body": {"number": 10}}, None))
