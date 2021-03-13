from random import randint


def generate_comment(user_id):
    random_number = randint(10000, 99999)
    result_comment = 'TTR' + str(user_id) + str(random_number)

    return result_comment
