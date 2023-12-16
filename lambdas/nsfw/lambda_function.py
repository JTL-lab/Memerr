from lambdas.nsfw.profile import Profile


def lambda_handler(event, context):
    """
    Lambda Fx to determine whether the user can toggle the nsfw view (button) based on age
    
    :param Either a Profile object or date_of_birth
    :return: JSON object can_toggle_nsfw boolean True/False
    """
    print(f'@lambda_handler: inputs {event}, {context}')
    date_of_birth = event.get('date_of_birth')

    if not date_of_birth:
        return {"error": "Date of birth not provided"}

    try:
        age = Profile.calculate_age(date_of_birth)
        can_toggle_nsfw = age >= 18

        return {
            "can_toggle_nsfw": can_toggle_nsfw
        }

    except ValueError as e:
        return {"error": str(e)}

"""
# test - assume Profile object passed in req
if __name__ == "__main__":
    test_event = {
        "email": "test@example.com",
        "phone": "1234567890",
        "username": "testuser",
        "password": "testpassword",
        "date_of_birth": "2000-01-01"
    }
    print(lambda_handler(test_event, None))
"""