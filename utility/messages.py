from config.settings import *
from functional.functions_old import *
from functional.functions_tt import *

# TODO сделать из линка на правила гиперссылку
START = f'🙋‍♂ Добро пожаловать в бот "temp_diz". Я создан для того, чтобы помогать тебе пиарить музон ' \
        f'в ТикТоке. Перед началом использования бота, обязательно прочитай небольшую ' \
        f'[инструкцию по использованию бота, а также правила]({LINK_TO_INTRODUCTION_AND_RULES})'

UPDATE = f'Привет еще раз!'

LITTLE_SUBCOIN_2 = '😳 Недостаточно Sub монет!'

SEND_YOUR_CHANNEL = '❕Для получения подписчиков в ваш канал:\n__1) Добавьте в него этого бота\n2) Отправьте сюда юзернейм вашего канала.__'

WRONG_TT_CLIP_LINK = 'Неправильная ссылка на тт клип, пришлите еще раз'

WRONG_MONEY_AMOUNT = 'Неверное введено количество желаемых денег к оплате. Пожалуйста, повторите ввод:'

WRONG_WITHDRAW_FUNDS = 'Неверное введено количество желаемых средств к выводу. ' \
                       'Пожалуйста, повторите ввод:'

WRONG_WITHDRAW_FUNDS_LOCATION = 'Неверное введен номер телефона или номер карты для вывода средств. ' \
                       'Пожалуйста, повторите ввод:'

def SEND_CLIP_COUNT(user_id, link):
    balance = user_balance_tt(user_id)

    send_sub_count = f'😀 Хорошо. Вы прислали {link}' \
                     f'\nТеперь отправьте нужное вам количество клипов на этот трек.' \
                     f'\nМинимальная цена за 1 клип - 10р' \
                     f'\nВаш баланс: {balance}' \
                     f'\nЕго хватит для заказа: {balance // CASH_MIN}'

    return send_sub_count


def TT_LINK_VIDEO_ERR():
    return 'Вы прислали некорректную ссылку на ТТ видео или вообще не ее! негодяй, меняй все!'


def TT_LINK_ACC_ERR():
    return 'Вы прислали некорректную ссылку на ТТ аккаунт или вообще не ее! негодяй, меняй все!'


def SEND_SUB_COUNT_1(m):
    send_sub_count = f'😀 Хорошо. Теперь отправьте нужное вам количество подписчиков.\n*Доступно:* {user_balance(m.from_user.id)}'
    return send_sub_count


def NEW_REFERAL(argument):
    new_referal = f'🥳 Поздравляем, у вас новый реферал!\nВсего рефералов: {referals(argument)}'
    return new_referal


def PROFILE(m):
    user_id = m.from_user.id

    profile = f'👤 Имя: {m.from_user.first_name}' \
              f'\n📟 ID: `{user_id}`' \
              f'\n💰 Баланс: {tt_user_balance(user_id)} RUB' \
              f'\nTT Аккаунт: {tt_account_link(user_id)}' \
              f'\n💪 Сделано клипов: {alltime_clips(user_id)}' \
              f'\n🤝 Получено клипов: {alltime_get_clips(user_id)}'
    # f'\n🤥 Оштрафовано всего на: {fine_count(m.from_user.id)} RUB' \
    # f'\n👣 Количество рефералов: {referals(m.from_user.id)}'

    return profile


GIVE_TT_VIDEO_LINK = '❕Для начала продвижения пришлите ссылку на видео в TikTok с вашим треком:'

# TODO старое
GIVE_CHANNEL_LINK = '''❕*Для начала продвижения:*

1) _Добавьте этого бота в свой канал (должен быть публичным);_
2) _Пришлите сюда юзернейм этого канала. Например:_ @hackerkg'''

CANCEL_TEXT = '🎳 Отменено'

BOT_NOT_IN_CHANNEL = '''❗️❗️❗️Вы не добавили бота в администраторы этого канала. Сначала добавьте бота в нужный вам канал, а уже потом пришлите его юзернейм❗️❗️❗️\n\n*После добавления бота в канал, пришлите сюда юзернейм этого канала!*'''

THIS_IS_NOT_CHANNEL = '''😡 *Это не канал!*\nПришлите сюда юзернейм канала, который вы хотите продвигать!'''

THIS_IS_NOT_TEXT = '''🤔 *Это не юзернейм канала!*\n\nПришлите сюда юзернейм канала который вы хотите продвигать.'''

NOT_TT_VIDEO = '''🤔 <b>Это не видео из ТТ!</b>\n\nПришлите сюда видео из ТТ, музыку которого хотите продвигать.'''


# TODO old
def CONFIRM_ADDING_CHANNEL(username, subcount, price):
    confirm_adding_channel = f'''Подтвердите добавление канала для продвижения:\n\n📻 Канал: @{username}\n\n📲 Количество подписчиков: {subcount}\n\n💳 Цена: {price} Sub монет'''
    return confirm_adding_channel


def CONFIRM_ADDING_VIDEO_TO_PROMO(clip_count, price):
    confirm_adding_channel = f'''Подтвердите добавление трека для продвижения:
                                \n📲 Количество клипов: {clip_count}
                                \n💳 Цена: {price} рублей'''

    return confirm_adding_channel


CHANNEL_ON_PROMOTION = "❗️Канал уже отправлен на продвижение!"

TT_VIDEO_ON_PROMOTION = "❗️Видео уже отправлено на продвижение!"

TT_ACC_DELETED = 'акк отвязан'

TT_ACC_ACCEPTED = 'акк привязан'

TT_ACC_WRONG = 'неправильная ссылка на тт акк'

CHANNEL_ON_PROMOTION_2 = '❌ Такой канал уже на продвижении! Дождитесь пока оно окончится, а потом попробуйте ещё раз.\nДобавьте другой канал или отмените действие:'

# TODO old
CHANNEL_SUCCESSFULLY_ADED = '👍 Канал успешно добавлен на продвижение.'

SUBSCRIBE_ON_THIS_CHANNEL = '''Подпишитесь на этот канал:\n1️⃣ Перейдите на канал 👇, подпишитесь ✔️ и пролистайте ленту вверх 🔝👁 (5-10 постов).\n2️⃣ Возвращайтесь⚡️сюда, чтобы получить вознаграждение.'''

NO_HAVE_CHANNELS_FOR_SUBSCRIBE = f"😔 Пока нет каналов для подписки. Но скоро будут!!\n\nА пока можете заглянуть в наш чатик: {LINK_TO_CHAT_OF_BOT}"

NO_TT_VIDEO_TO_PROMO = f"😔 Пока нет клипов для продвижения. Но скоро будут! Возвращайтесь через 10 минут."

# TODO добавить в хуйню ссылку на видос
RECORD_THIS_TT_VIDEO = '''Снимите видео в TikTok:
                        \n1. Перейдите на видео по ссылке, выбирите трек из видео и снимите свое видео под него.
                        \n2. Возвращайтесь сюда, чтобы получить вознаграждение.
                        \n3. Чтобы пропустить клип, нажмите Заработать еще раз'''

TT_ACCOUNT = '''Пришлите ссылку на свой TikTok аккаут:
                \nНастройки профиля -> Поделиться профилем -> скопировать ссылку'''

CLIP_SUCCESSFULLY_ADDED = '👍 Клип успешно добавлен на продвижение.'


def CHANNEL_WAS_DEL_FROM_CHANNEL(id, link_to_rules):
    message = f'❗️Вам экстренное сообщение.\n\nБыло обнаружено, что бот был удален из вашего канала (id канала: `{id}`)\n😡 В качестве штрафа за нарушение [правил]({link_to_rules}), продвижение канала остановлено и только половина из неиспользованных для продвижения этого канала Sub Coin, возвращены вам на баланс.\nПроверка юзеров на отписку также остановлена.'
    return message


def SUBSCRIBE_IS_SUCCESSFULLY(username):
    message = f'👍 Вы успешно подписались на канал: @{username}\nВам на баланс начислено 1 Sub Coin 💠.'
    return message


def YOU_ARE_LATE_FOR_SUBS(username):
    message = f'☹️ Вы не успели подписаться на канал, прежде чем его продвижение окончилось.\nМожете отписаться от этого канала: @{username}'
    return message


YOU_DONT_COMPLETE_SUBS = '😡 Вы ещё не подписались на этот канал!'


def PARTNER_PROGRAM(username_of_bot, user_id, ref_count):
    message = f'🤩 Приглашайте в бота друзей и знакомых по своей реферальной ссылке и получайте по 2 Sub монет за каждого.' \
              f'\n👥 Вы уже пригласили: {ref_count}\n👣 *Ваша реферальная ссылка:* https://t.me/{username_of_bot}?start={user_id}'
    return message


SELECT_ADMIN_MENU_BUTTON = '🛠 Выберите пункт меню:'

START_COLLECT_STAT = '⏱ Начинаю сбор статистики...'

TT_VIDEO_SKIPPED = 'Видео пропущено'

MONEY_EARNED = 'Молодес ты скинул бабки адресату ВЕЛЛ ДОНЕ'

MONEY_NOT_EARNED = 'Бабки не получены'


def MONEYS(payment_money_amount, payment_comment):
    qiwi_number = '+79100938360'
    message = f'Столько то денег будет добавлено на акк {payment_money_amount}, ' \
              f'вот с таким комментом надо отправить {payment_comment} на вот этот номер QIWI {qiwi_number}'
    return message


TT_CLIP_CHECKING = 'Подождите 10 минут для проверки. Пока можете записать клипы на другие треки!'


def STATISTICS(all, die):
    alive = all - die
    message = f'😅 Всего юзеров: {all}\n\n😵 Мёртвые: {die}\n\n🤠 Живые: {alive}'
    return message


SEND_MESSAGE_FOR_SEND = '🖋 Отправьте _текст/фото/видео/gif/файл_ для рассылки.'


def MAILING_END(all, die):
    alive = all - die
    message = f'✅ Рассылка окончена.\n\n🤠 Успешно доставлено сообщений: {alive}\n\n😢 Недоставлено сообщений: {die}'
    return message


# TODO допилить инструкцию
TOP_UP_BALANCE = 'Инструкция для пополнения баланса:\nВведите сколько хотите закинуть!'


def WITHDRAW_FUNDS(balance):
    message = f'Вывод средств доступен при наличии 200 RUB на балансе.\n' \
              f'На вашем счету сейчас {balance} RUB\n\n' \
              f'Напишите сумму, которую хотите вывести:'

    return message


def WITHDRAW_FUNDS_WHERE(funds_amount):
    message = f'Отлично! Вы хотите вывести {funds_amount} с вашего аккаунта.\n' \
              f'Укажите номер телефона для вывода через QIWI Wallet или номер карты для перевода через банк:'

    return message


def WITHDRAW_FUNDS_SUCCESS_QUESTION(user_id, funds_amount):
    message = f'Отлично! Вы хотите вывести {funds_amount} с вашего аккаунта.\n' \
              f'Укажите номер телефона для вывода через QIWI Wallet или номер карты для перевода через банк:'

    return message


SEND_USER_FOR_UBAN = '❓Для бана человека отправьте:\n\n<Id человека которого нужно забанить> 0\n\n❓Для разбана человека отправьте:\n\n<Id человека которого нужно разбанить> 1'

NOT_INTEGER = 'Одно из передаваемых значений не число!'

LITTLE_VALUE = '😡 Вы должны были отправить два значения разделяя их пробелом!'

YOU_WAS_BANNED = '🥳 Поздравляю! Вас забанили в этом боте. Теперь вы не сможете им пользоваться.'

YOU_WAS_HACK_ME = '🤭 Вы меня взломали! Что мне теперь делать?'

SEND_USER_FOR_CHANGE_BALANCE = '''❗️Для изменения баланса человека отправьте:\n\n 
<id человека которому нужно изменить баланс>пробел<значение, на которое хотите изменить баланс>'''


def SUBSCRIPTION_VIOLATION(username, sub_term, count_of_fine):
    message = f'😡 Вы отписались от канала @{username} раньше чем через {sub_term} дней!\n\nВ качестве штрафа с вашего баланса снято {count_of_fine} Sub монет 💠.'
    return message


YOU_DID_THIS = '🙂 Самый хитрый?\nТы ведь уже выполнял это задание)'
