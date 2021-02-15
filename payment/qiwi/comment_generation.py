from random import randint


def generate_comment(user_id):
    random_number = randint(100000, 999999)
    result_comment = 'DIZ' + str(user_id) + str(random_number)

    return result_comment
