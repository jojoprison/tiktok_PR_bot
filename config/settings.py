# dev - temp_diz
BOT_TOKEN_DEV = ''
BOT_TOKEN_PUB = ''

# TODO куки для тиктока (обновлять) / обновляется редко
TT_VERIFY_FP = 'verify_knkfa9v6_LjWvDJpI_xIom_4Fiq_8WeV_gNJixQ1OtNSD'

TT_COOKIE = {
        "s_v_web_id": TT_VERIFY_FP,
        "tt_webid": '6948885120527418885'
}

# админы бота через запятую
BOT_ADMINS = []

# минимум бабок для раскрутки трека (1 клип)
CASH_MIN = 10

# оплата за один записанный клип
CLIP_PAYMENT = 9

# реферальный бонус (рубли)
REF_BONUS = 1

# TODO куки для тиктока (обновлять) / обновляется редко
TT_VERIFY_FP = ''

TT_COOKIE = {
        "s_v_web_id": TT_VERIFY_FP,
        "tt_webid": ''
}

LOG_CONFIG_DICT = {
        'version': 1,
        'handlers': {
            'default_handler': {
                'class': 'logging.FileHandler',
                'formatter': 'default_formatter',
                'filename': 'main.log'
            }
        },
        'loggers': {
            'bot': {
                'handlers': ['default_handler'],
                'level': 'INFO',
            }
        },
        'formatters': {
            'default_formatter': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S %z'
            }
        }
    }
