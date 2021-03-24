# dev
BOT_TOKEN = '1571069556:AAEfBY3xH_1zwKCSJmt0UBfO2hyJ7OR_PeI'
# BOT_TOKEN = '1666304092:AAGjaMzajP4Wmq_LHuWLNgwIfXrLX6YttAM'

# админы бота через запятую
BOT_ADMINS = [92957440, 450914065, 855235999]

# минимум бабок для раскрутки трека (1 клип)
CASH_MIN = 10

# оплата за один записанный клип
CLIP_PAYMENT = 9

# реферальный бонус (рубли)
REF_BONUS = 1

# TODO куки для тиктока (обновлять)
TT_VERIFY_FP = 'verify_klv5c5xg_nEikqRKz_up6a_4o0n_Bzh2_qD4CuJUGbEDh'

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
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
    }
