import re


def valid_withdraw_number(withdraw_number):
    withdraw_number_len = len(withdraw_number)

    if withdraw_number_len == 16:
        card_pattern = '^([0-9]{4})-?([0-9]{4})-?([0-9]{4})-?([0-9]{4})$'

        """Returns `True' if the sequence is a valid credit card number.

            A valid credit card number
            - must contain exactly 16 digits,
            - must start with a 4, 5 or 6 
            - must only consist of digits (0-9) or hyphens '-',
            - may have digits in groups of 4, separated by one hyphen "-". 
            - must NOT use any other separator like ' ' , '_',
            - must NOT have 4 or more consecutive repeated digits.
        """

        match = re.match(card_pattern, withdraw_number)

        if match is None:
            return False

        return True, 'bank_card'
    # учитываем плюсик в длине номера
    else:
        clear_phone = re.sub(r'\D', '', withdraw_number)
        result = re.match(r'^[78]?\d{10}$', clear_phone)

        return result, 'qiwi'


if __name__ == '__main__':
    phones_str = str('+79160000000; 9160000000; 8(916)000-00-00; +7(916)000-00-00; (916)000-00-00; '
                     '8 (916) 000-00-00; +7 (916) 000-00-00; '
                     '(916) 000-00-00; 8(916)0000000; '
                     '+7(916)0000000; (916)0000000; 8-916-000-00-00; +7-916-000-00-00; 916-000-00-00')

    phones = re.split(r' *; *', phones_str, flags=re.M)

    for phone in phones:
        valid_withdraw_number(phone)
