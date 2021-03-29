import logging
import logging.config
import random
import time
import datetime

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.utils import executor
from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.exceptions import UserDeactivated
from aiogram.utils.helper import Helper, ListItem

from db.write_to_excel import save_data_into_excel
from payment.qiwi.payment import *
from utility.messages import *
from utility.validation import *
from config.settings import LOG_CONFIG_DICT

loop = asyncio.get_event_loop()


def choose_bot_token():
    # меняем токен бота в зависимости от нужды, вводим через консоль число
    console_input_data = input('enter number of bot_token (0 - dev, 1 - pub)')

    # флаг цикла корректности введенного числа
    token_invalid = True
    token_chooser = None

    while token_invalid:
        try:
            token_chooser = int(console_input_data)
            token_invalid = False
        except Exception as e:
            print(e)
            print('invalid token number, enter valid number')

    if token_chooser == 0:
        bot_token = BOT_TOKEN_DEV
        print('DEV token took')
    else:
        bot_token = BOT_TOKEN_PUB
        print('PUB token took')

    return bot_token


bot = Bot(token=choose_bot_token(), loop=loop)

dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())


# TODO придумать че делать со стейтами
class UserStates(Helper):
    GET_CHANNEL_TO_UP = ListItem()
    GET_SUB_COUNT = ListItem()
    CONFIRMATION = ListItem()
    GET_MSG_FOR_MAIL = ListItem()
    ADMIN_BAN = ListItem()
    ADMIN_CHANGE_BALANCE = ListItem()


main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add('Заработать', 'Заказать')
main_menu.add('👤 Профиль', 'Партнёрская программа')
main_menu.add('Канал с выплатами')

admin_menu = InlineKeyboardMarkup()

statistics_bt = InlineKeyboardButton(text='📊 Статистика', callback_data='stat')
mail_bt = InlineKeyboardButton(text='✉️Рассылка', callback_data='mail')
give_uban_bt = InlineKeyboardButton(text='🚷 Выдать бан/разбан', callback_data='uban')
change_balance_bt = InlineKeyboardButton(text='💳 Изменить баланс', callback_data='chb')
unverified_tasks = InlineKeyboardButton(text='Вывести деньги пользователю', callback_data='admin_withdraw')
get_user_list = InlineKeyboardButton(text='Выгрузить данные базы', callback_data='admin_get_db_data')
get_logs = InlineKeyboardButton(text='Выгрузить логи', callback_data='admin_get_logs')

admin_menu.add(statistics_bt, mail_bt)
admin_menu.add(give_uban_bt, change_balance_bt)
admin_menu.add(unverified_tasks, get_user_list)
admin_menu.add(get_logs)

cancel_menu = InlineKeyboardMarkup()
cancel_bt = InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel')
cancel_menu.add(cancel_bt)

logger_name_main = 'bot.main'


def get_logger_name_main():
    logging.config.dictConfig(LOG_CONFIG_DICT)

    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.datetime.now().astimezone(moscow_tz)
    # now.timetuple()

    logging.Formatter.converter = time.gmtime

    return logger_name_main


# TODO Доделать таймер
def update_tt_usernames(time_interval):
    while True:
        print('Doing timer work')
        update_tt_acc_username_all()
        time.sleep(time_interval)


async def pay_user_for_tasks(user_id, delay):
    await asyncio.sleep(delay)

    logger = logging.getLogger(f'{get_logger_name_main()}.{pay_user_for_tasks.__name__}')
    logger.info('Paying completed tasks for user: ' + str(user_id))

    payment_sum = await pay_all_completed_user_tasks(user_id)

    return payment_sum


# TODO Доделать таймер
async def return_clip_int_queue(user_id, clip_id, delay):
    await asyncio.sleep(delay)

    logger = logging.getLogger(f'{get_logger_name_main()}.{return_clip_int_queue.__name__}')
    logger.info('Wait for clip in queue for : ' + str(delay) + ', clip_id = ' + str(clip_id))

    await is_return_clip_in_queue(user_id, clip_id)

    return True


@dp.message_handler(commands=['start'])
async def command_start(m: types.Message):
    user_id = int(m.from_user.id)
    username = m.from_user.username

    state = dp.current_state(user=user_id)
    await state.reset_state()

    if await is_user_in_db_tt(user_id) < 1:
        argument = m.get_args()

        logger = logging.getLogger(f'{get_logger_name_main()}.{command_start.__name__}')

        try:
            if (argument is not None) and (argument.isdigit() is True) and (await is_user_in_db_tt(int(argument))) == 1:
                logger.info(f'try to reg user {user_id} by referral {argument}')

                argument = int(argument)
                await add_user_to_db_tt(user_id, username, ref_father=argument)

                logger.info(f'user {user_id} registered with by referral {argument}')

                await m.reply(START, reply=False, parse_mode='HTML', reply_markup=main_menu)
                await bot.send_message(text=await NEW_REFERRAL(argument), chat_id=argument)
            else:
                await add_user_to_db_tt(user_id, username)

                logger.info(f'user {argument} default registered')

                await m.reply(START, reply=False, parse_mode='HTML', reply_markup=main_menu)

        except Exception as e:
            logger.error(f'{user_id} got ex: {e}')
            await m.reply('Произошла ошибка, нажмите кнопку "Отмена"', reply_markup=cancel_menu)
    else:
        await m.reply(UPDATE, reply=False, parse_mode='HTML', reply_markup=main_menu)


@dp.message_handler(commands=['help'])
async def command_help(m: types.Message):
    user_id = m.from_user.id

    logger = logging.getLogger(f'{get_logger_name_main()}.{command_help.__name__}')
    logger.info(f'user {user_id} learn rules')

    state = dp.current_state(user=user_id)
    await state.reset_state()

    await m.reply(HELP, reply=False, parse_mode='HTML', reply_markup=main_menu)


@dp.message_handler(lambda m: m.from_user.id in BOT_ADMINS, commands=['admin'])
async def command_admin(m: types.Message):
    await m.reply(SELECT_ADMIN_MENU_BUTTON, reply=False, reply_markup=admin_menu)


@dp.message_handler(lambda m: m.from_user.id not in BOT_ADMINS, commands=['admin'])
async def command_not_admin(m: types.Message):
    logger = logging.getLogger(f'{get_logger_name_main()}.{command_not_admin.__name__}')
    logger.warning(f'user {m.from_user.id} try to get admin panel')

    await m.reply(YOU_WAS_HACK_ME, reply=False)


@dp.message_handler(lambda m: m.text == '👤 Профиль', state='*')
async def profile_button_handle(m: types.Message):
    state = dp.current_state(user=m.from_user.id)
    await state.reset_state()

    balance_manipulations = InlineKeyboardMarkup()
    balance_manipulations.add(
        InlineKeyboardButton(text='Пополнить баланс', callback_data='top_up_balance'),
        InlineKeyboardButton(text='Вывести средства', callback_data='withdraw_funds'))

    # TODO добавить проверку есть ли пользователь в базе
    await m.reply(await PROFILE(m), reply=False, parse_mode='HTML', reply_markup=balance_manipulations)


@dp.message_handler(lambda m: m.text == 'Заказать')
async def add_tt_video_handle(m: types.Message):
    state = dp.current_state(user=m.from_user.id)
    await state.set_state('GET_TT_VIDEO')
    await m.reply(GIVE_TT_VIDEO_LINK, reply=False, parse_mode='HTML', reply_markup=cancel_menu)


@dp.message_handler(content_types=['text'], state='GET_TT_VIDEO')
async def tt_video_handle(m: types.Message):

    logger = logging.getLogger(f'{get_logger_name_main()}.{tt_video_handle.__name__}')
    user_id = m.from_user.id

    try:
        if m.content_type == 'text':
            clip_link = m.text

            if valid_tt_link(clip_link):
                logger.info(f'user {user_id} wanna add {clip_link}')

                # TODO заглушка
                # tt_clip_data = get_music_id_from_clip_tt(clip_link)
                # tt_clip_id = clip_data.get('clip_id')
                # tt_music_id = clip_data.get('music_id')

                tt_clip_id = 1
                tt_music_id = 2

                # TODO сохранять видос/линк на него в БД
                order_id = await save_tt_clip(client=user_id, clip_link=clip_link,
                                              clip_id=tt_clip_id, music_id=tt_music_id)

                logger.info(f'clip added {clip_link}')

                cancel_promotion = InlineKeyboardMarkup()
                # TODO добавить эту штуку для удаления видоса в случае нажатия кнопки отмена
                cancel_promotion.add(
                    InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_' + str(order_id)))

                await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)
                await m.reply(await SEND_CLIP_COUNT(user_id, clip_link), reply=False, parse_mode='HTML',
                              reply_markup=cancel_promotion)

                state = dp.current_state(user=user_id)

                # TODO поменять статус и начать пиар видео
                await state.set_state('SEND_CLIP_COUNT')
            else:
                logger.info(f'user {user_id} FALL with adding clip {clip_link}')

                cancel = InlineKeyboardMarkup()
                cancel.add(
                    InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel'))

                await bot.delete_message(message_id=m.message_id - 1, chat_id=user_id)
                await m.reply(WRONG_TT_CLIP_LINK, reply=False, parse_mode='HTML',
                              reply_markup=cancel)

        else:
            await bot.delete_message(message_id=m.message_id - 1, chat_id=user_id)

            cancel_promotion = InlineKeyboardMarkup()
            # TODO сделать обработку этой кнопки отмены
            cancel_promotion.add(
                InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel'))

            # TODO Добраотка
            await m.reply(TT_LINK_VIDEO_ERR(), reply=False, parse_mode='HTML',
                          reply_markup=cancel_menu)

    except Exception as e:
        logger.error(f'{user_id} got ex: {e}')
        await m.reply('Произошла ошибка, нажмите кнопку "Отмена"', reply_markup=cancel_menu)


# TODO сделать метод обработки ссылки
def valid_tt_link(link):
    netloc = url_parser.urlparse(link).netloc

    return netloc == 'www.tiktok.com' or netloc == 'vm.tiktok.com'


# TODO сделать метод проверки аккаута TT
def check_tt_account_link(link):
    netloc = url_parser.urlparse(link).netloc

    if netloc == 'www.tiktok.com' or netloc == 'vm.tiktok.com':
        try:
            get_tt_acc_name(link)
        except Exception as e:
            return False

        return True
    else:
        return False


async def tt_acc_not_exist(user_id):
    link = await get_tt_account_link(user_id)

    # проверяет есть ли в базе вообще что-то стринговое
    return not isinstance(link, str)


@dp.message_handler(lambda m: m.text == 'Заработать', state='*')
async def get_money(m: types.Message):
    user_id = m.from_user.id

    state = dp.current_state(user=user_id)
    await state.reset_state()

    logger = logging.getLogger(f'{get_logger_name_main()}.{get_money.__name__}')

    if await tt_acc_not_exist(user_id):
        logger.info(f'user {user_id} dont have tiktok_username name in db')

        await state.set_state('REG_TT_ACCOUNT')

        await m.reply(TT_ACCOUNT, reply=False, parse_mode='HTML', reply_markup=cancel_menu)
    else:
        # стейт мешает потом опять зайти в эту функцию
        # state = dp.current_state(user=user_id)
        # await state.set_state('GET_MONEY')

        logger.info(f'user {user_id} get clips for work')

        try:
            clips_info = await get_clips_for_work(user_id)

            logger.info(f'user {user_id} got clips for work')

            if clips_info.get('clips_exist'):
                logger.info(f'user {user_id} got clips and exist to work /')

                await m.reply(clips_info.get('reply_msg'),
                              reply_markup=clips_info.get('inline_kb'),
                              reply=False)
            else:
                logger.info(f'user {user_id} got clips, no working ><')

                await m.reply(clips_info.get('reply_msg'),
                              reply=False)

        except Exception as e:
            logger.error(f'{user_id} got ex: {e}')
            await m.reply('Произошла ошибка, нажмите кнопку "Отмена"', reply_markup=cancel_menu)


async def get_clips_for_work(user_id):
    # все видосы для продвижения
    clip_list = await clips_for_work(user_id)

    result_info = {}

    if clip_list == 0:
        result_info['clips_exist'] = False
        result_info['reply_msg'] = NO_TT_VIDEO_TO_PROMO

        return result_info

    skipped_videos = await get_skipped_videos(user_id)

    clip_id_set = set(clip_list.keys())
    skipped_clip_id_set = set(skipped_videos.keys())

    shown_clip_id_set = clip_id_set.difference(skipped_clip_id_set)

    shown_clip_dict = {}

    for clip_id in shown_clip_id_set:
        shown_clip_dict[clip_id] = clip_list[clip_id]

    # проверяем, пустой ли
    if shown_clip_dict:
        # выбираем случайный видос
        random_clip_order_id = random.choice(list(shown_clip_dict))
        tt_video_link = shown_clip_dict[random_clip_order_id]

        tt_menu = InlineKeyboardMarkup()
        tt_menu.add(InlineKeyboardButton(text='Перейти к TT видео с треком',
                                         url=tt_video_link))
        # TODO потом сделать метод проверки видоса через TT API СДЕЛАТЬ ПЕРЕДЫШКУ 1-2мин и потом пополнять баланс
        tt_menu.add(InlineKeyboardButton(text='Проверить',
                                         callback_data='check_clip_' + str(random_clip_order_id)))
        tt_menu.add(InlineKeyboardButton(text='Пропустить',
                                         callback_data='skip_' + str(random_clip_order_id)))

        result_info['clips_exist'] = True
        result_info['reply_msg'] = RECORD_THIS_TT_VIDEO
        result_info['inline_kb'] = tt_menu

        # TODO это в случае ошибки какая-то херня с возвратом денег клиенту
        # writer = edit_promo_status(video_list[video_to_promo], 0)
        # await bot.send_message(writer, CHANNEL_WAS_DEL_FROM_CHANNEL(id, LINK_TO_INTRODUCTION_AND_RULES))

    else:
        result_info['clips_exist'] = False
        result_info['reply_msg'] = NO_TT_VIDEO_TO_PROMO

    return result_info


@dp.message_handler(state='REG_TT_ACCOUNT')
async def tt_username_connect(m: types.Message):
    logger = logging.getLogger(f'{get_logger_name_main()}.{tt_username_connect.__name__}')

    user_id = m.from_user.id

    try:
        logger.info(f'user {user_id} try to connect tiktok account link to db')

        if m.content_type == 'text':
            tt_acc_link = m.text

            logger.info(f'{user_id} parse tiktok account link: {tt_acc_link}')

            # TODO доделать парсер аккаута
            if check_tt_account_link(tt_acc_link):
                logger.info(f'{user_id} save tiktok account link to db: {tt_acc_link}')

                # TODO сохранять ссылку на акк в БД юзера
                return_tt_acc = await add_tt_acc_to_user(user_id, tt_acc_link)

                logger.info(f'{user_id} connect tt account link with db {tt_acc_link}')

                # cancel_promotion = InlineKeyboardMarkup()
                # TODO добавить эту штуку для отвязки акка в случае нажатия кнопки отмена
                # cancel_promotion.add(
                #     InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_tt_acc_' + str(user_id)))

                await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)
                await m.reply(TT_ACC_ACCEPTED, reply=False, parse_mode='HTML')
                # reply_markup=cancel_promotion)
            else:
                logger.info(f'{user_id} invalid tiktok account link')

                await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)
                await m.reply(TT_ACC_WRONG, reply=False, parse_mode='HTML')

            state = dp.current_state(user=m.from_user.id)
            await state.reset_state()
        else:
            logger.info(f'{user_id} send incorrect tt acc link: {m.text}')

            await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)

            cancel_promotion = InlineKeyboardMarkup()
            # TODO сделать обработку этой кнопки отмены
            cancel_promotion.add(
                InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel'))

            # TODO Добраотка
            await m.reply(TT_LINK_ACC_ERR(), reply=False, parse_mode='HTML',
                          reply_markup=cancel_menu)

    except Exception as e:
        logger.error(f'{user_id} got ex: {e}')
        await m.reply('Произошла ошибка, нажмите кнопку "Отмена"', reply_markup=cancel_menu)


# TODO доделать покупку клипов
@dp.message_handler(state='SEND_CLIP_COUNT')
async def send_clip_count(m: types.Message):
    logger = logging.getLogger(f'{get_logger_name_main()}.{send_clip_count.__name__}')

    user_id = m.from_user.id

    if (m.content_type == 'text') and (m.text.isdigit() is True) and (
            int(m.text) >= 1) and await get_user_balance_tt(user_id) >= int(m.text) * CASH_MIN:

        logger.info(f'{user_id} sent valid clip_count')

        video_to_promo_count = int(m.text)
        logger.info(f'{user_id} update clip_order_goal {video_to_promo_count}')

        try:
            # TODO передавать order_id через внутреннюю переменную state
            order_id = await update_tt_video_goal(video_to_promo_count)

            logger.info(f'{user_id} clip_order_goal in clip {order_id} updated {video_to_promo_count}')

            confirmation_menu = InlineKeyboardMarkup()
            confirmation_menu.add(
                InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_' + str(order_id)),
                InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm_' + str(order_id)))

            state = dp.current_state(user=user_id)
            await state.set_state('CONFIRMATION')

            await bot.delete_message(message_id=m.message_id - 1, chat_id=user_id)

            # TODO выводить ссылку на видос
            await m.reply(
                CONFIRM_ADDING_VIDEO_TO_PROMO(video_to_promo_count, video_to_promo_count * CASH_MIN),
                reply=False,
                reply_markup=confirmation_menu)

        except Exception as e:
            logger.error(f'{user_id} got ex: {e}')
            await m.reply('Произошла ошибка, нажмите кнопку "Отмена"', reply_markup=cancel_menu)

    else:
        logger.info(f'{user_id} not enough balance to PR clip')

        # TODO придумать передачу этого order_id через стейт машину
        order_id = await get_video_stat(user_id)

        # TODO убрать кнопку и удалять видос из базы или ставить статус говна
        cancel_pay_menu = InlineKeyboardMarkup()
        cancel_pay_menu.add(
            InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_' + str(order_id)))

        await m.reply(INSUFFICIENT_FUNDS, reply=False, reply_markup=cancel_pay_menu)


# пополнение баланса
@dp.message_handler(content_types=types.ContentType.ANY, state='TOP_UP_BALANCE')
async def top_up_balance(m: types.Message):
    logger = logging.getLogger(f'{get_logger_name_main()}.{top_up_balance.__name__}')

    user_id = m.from_user.id

    logger.info(f'{user_id} top up balance')

    bot_last_message_id = m.message_id - 1

    if m.content_type == 'text':
        money_amount = int(m.text)

        logger.info(f'{user_id} add user payment with {money_amount} money')

        try:
            payment_info = await add_user_payment(user_id, money_amount)
            payment_comment = payment_info[0]
            payment_id = payment_info[1]

            logger.info(f'{user_id} user payment {payment_id} with {money_amount}')

            # TODO придумать че делать, когда отправляется список объектов
            await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
            # await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)

            payment_menu = InlineKeyboardMarkup()
            payment_menu.add(
                InlineKeyboardButton(text='Проверить оплату', callback_data='check_payment_' + str(payment_id)),
                InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel'))

            state = dp.current_state(user=m.from_user.id)
            await state.set_state('CONFIRM_TOP_UP_BALANCE')

            # TODO запищивать в стейт машину, чтоб в ответе на неправильное сообщение реплаить на него
            top_up_balance_message_id = await m.reply(
                MONEYS(money_amount, payment_comment),
                reply=False, reply_markup=payment_menu, parse_mode='HTML')

        except Exception as e:
            logger.error(f'{user_id} got ex: {e}')
            await m.reply('Произошла ошибка, нажмите кнопку "Отмена"', reply_markup=cancel_menu)
    else:
        logger.info(f'{user_id} invalid money_amount {m.text}')

        await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)

        await m.reply(WRONG_MONEY_AMOUNT, reply=False, reply_markup=cancel_menu)


# подтверждение пополнения баланса
@dp.message_handler(content_types=types.ContentType.ANY, state='CONFIRM_TOP_UP_BALANCE')
async def confirm_top_up_balance(m: types.Message):
    logger = logging.getLogger(f'{get_logger_name_main()}.{confirm_top_up_balance.__name__}')

    user_id = m.from_user.id

    logger.info(f'{user_id} confirm again money_amount {m.text}')

    await bot.send_message(chat_id=user_id,
                           text='Нажмите одну из кнопок операций с пополнением баланса выше',
                           reply_to_message_id=m.message_id - 1)


# проверка данных для вывода средств
@dp.message_handler(content_types=types.ContentType.ANY, state='WITHDRAW_FUNDS_VALIDATION')
async def withdraw_funds_validation(m: types.Message):
    logger = logging.getLogger(f'{get_logger_name_main()}.{withdraw_funds_validation.__name__}')

    user_id = m.from_user.id

    logger.info(f'{user_id} try to valid withdraw funds {m.text}')

    bot_last_message_id = m.message_id - 1

    if m.content_type == 'text':
        funds_amount = m.text

        try:
            funds_amount = int(funds_amount)

            logger.info(f'{user_id} get user balance')

            balance = await get_user_balance_tt(user_id=user_id)

            if balance >= funds_amount:
                if funds_amount >= 200:
                    logger.info(f'{user_id} add withdraw funds')

                    await add_withdraw_funds(user_id, funds_amount)

                    # TODO придумать че делать, когда отправляется список объектов
                    # TODO вылезает ошибка когда я ищу предыдущее сообение, если функцией пользуются несколько челов
                    await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
                    # await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)

                    state = dp.current_state(user=user_id)
                    await state.set_state('WITHDRAW_FUNDS_LOCATION')

                    await m.reply(WITHDRAW_FUNDS_WHERE(funds_amount),
                                  reply=False, reply_markup=cancel_menu)
                else:
                    logger.info(f'{user_id} withdraw funds less than 200')

                    await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
                    await m.reply(WITHDRAW_SUM_LESS_200, reply=False, reply_markup=cancel_menu)
            else:
                logger.info(f'{user_id} withdraw funds not enough: balance = {balance}, '
                            f'funds_amount = {funds_amount}')

                await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
                await m.reply(INSUFFICIENT_FUNDS_TO_WITHDRAW, reply=False, reply_markup=cancel_menu)

        except ValueError:
            logger.error(f'{user_id} withdraw funds {funds_amount}')

            await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
            await m.reply(WRONG_WITHDRAW_FUNDS, reply=False, reply_markup=cancel_menu)
    else:
        logger.info(f'{user_id} invalid withdraw funds {m.text}')

        await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
        await m.reply(WRONG_WITHDRAW_FUNDS, reply=False, reply_markup=cancel_menu)


# выбор способа вывода средств
@dp.message_handler(content_types=types.ContentType.ANY, state='WITHDRAW_FUNDS_LOCATION')
async def withdraw_funds_location(m: types.Message):
    logger = logging.getLogger(f'{get_logger_name_main()}.{withdraw_funds_location.__name__}')

    user_id = m.from_user.id

    bot_last_message_id = m.message_id - 1

    if m.content_type == 'text':
        withdraw_funds_number = m.text

        logger.info(f'{user_id} try to valid withdraw funds location number: {withdraw_funds_number}')

        try:
            withdraw_number_validation = valid_withdraw_number(withdraw_funds_number)

            if withdraw_number_validation[0]:
                last_withdraw_id = await get_last_withdraw()

                logger.info(f'{user_id} update withdraw location number')

                await update_withdraw_location(last_withdraw_id, withdraw_number_validation[1],
                                               withdraw_funds_number)

                logger.info(f'{user_id} withdraw location number updated')

                # TODO придумать че делать, когда отправляется список объектов
                await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)

                withdraw_success_question = InlineKeyboardMarkup()
                withdraw_success_question.add(
                    InlineKeyboardButton(text='Вывести', callback_data='withdraw_funds_' + str(last_withdraw_id)),
                    InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel'))

                state = dp.current_state(user=m.from_user.id)
                await state.set_state('WITHDRAW_FUNDS_WAIT_MONEY')

                await m.reply(WITHDRAW_FUNDS_SUCCESS_QUESTION(withdraw_funds_number),
                              reply=False, reply_markup=withdraw_success_question)
            else:
                logger.info(f'{user_id} withdraw location number invalid {withdraw_funds_number}')

        except Exception as e:
            logger.error(f'{user_id} got ex: {e}')
            await m.reply('Произошла ошибка, нажмите кнопку "Отмена"', reply_markup=cancel_menu)
    else:
        logger.info(f'{user_id} text is not text: {m.content_type}')

        await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
        await m.reply(WRONG_WITHDRAW_FUNDS_LOCATION, reply=False, reply_markup=cancel_menu)


# админская способность рассылки
@dp.message_handler(content_types=['text', 'video', 'photo', 'document', 'animation'], state='GET_MSG_FOR_MAIL')
async def mailing(m: types.Message):
    state = dp.current_state(user=m.from_user.id)
    await state.reset_state()

    users = await get_all_user_id()

    if m.content_type == 'text':
        all_users = 0
        blocked_users = 0

        for user_id in users:
            try:
                await bot.send_message(user_id, m.html_text, parse_mode='HTML')
                all_users += 1
                await asyncio.sleep(0.3)
            except BotBlocked:
                blocked_users += 1
            except Exception as e:
                print(e)

        await m.reply(MAILING_END(all_users, blocked_users), reply=False)
    if m.content_type == 'photo':
        all_users = 0
        blocked_users = 0
        for x in users:
            try:
                await bot.send_photo(x[0], photo=m.photo[-1].file_id, caption=m.html_text, parse_mode='HTML')
                all_users += 1
                await asyncio.sleep(0.3)
            except BotBlocked:
                blocked_users += 1
        await m.reply(MAILING_END(all_users, blocked_users), reply=False)
    if m.content_type == 'video':
        all_users = 0
        blocked_users = 0
        for x in users:
            try:
                await bot.send_video(x[0], video=m.video.file_id, caption=m.html_text, parse_mode='HTML')
                all_users += 1
                await asyncio.sleep(0.3)
            except BotBlocked:
                blocked_users += 1
        await m.reply(MAILING_END(all_users, blocked_users), reply=False)
    if m.content_type == 'animation':
        all_users = 0
        blocked_users = 0
        for x in users:
            try:
                await bot.send_animation(x[0], animation=m.animation.file_id)
                all_users += 1
                await asyncio.sleep(0.3)
            except BotBlocked:
                blocked_users += 1
        await m.reply(MAILING_END(all_users, blocked_users), reply=False)
    if m.content_type == 'document':
        all_users = 0
        blocked_users = 0
        for x in users:
            try:
                await bot.send_document(x[0], document=m.document.file_id)
                all_users += 1
                await asyncio.sleep(0.3)
            except BotBlocked:
                blocked_users += 1
        await m.reply(MAILING_END(all_users, blocked_users), reply=False)


@dp.message_handler(lambda m: m.text == 'Партнёрская программа', state='*')
async def referral_button(m: types.Message):
    state = dp.current_state(user=m.from_user.id)
    await state.reset_state()

    user_id = m.from_user.id

    get_bot = await bot.get_me()
    await m.reply(PARTNER_PROGRAM(get_bot.username, user_id,
                                  await get_referrals_count(user_id)),
                  reply=False, parse_mode='HTML')


# канал где дайм делает делишки))
@dp.message_handler(lambda m: m.text == 'Канал с выплатами')
async def referral_button(m: types.Message):
    await m.reply(CHANNEL_FOR_MONEY, reply=False, parse_mode='HTML')


@dp.message_handler(lambda m: m.from_user.id in BOT_ADMINS, content_types=['text'], state='ADMIN_CHANGE_BALANCE')
async def handle_user_for_chb(m: types.Message):
    change_balance_request = m.text.split(' ')

    if len(change_balance_request) == 2:
        user_id = change_balance_request[0]
        balance_increase = change_balance_request[1]

        if user_id.isdigit() and balance_increase.lstrip('-').isdigit():
            user_id = int(user_id)
            balance_increase = int(balance_increase)

            increase_balance_result = await increase_balance_tt(user_id, balance_increase)

            await m.reply(increase_balance_result, reply=False)
        else:
            await m.reply(NOT_INTEGER, reply=False)
    else:
        await m.reply(LITTLE_VALUE, reply=False)

    state = dp.current_state(user=m.from_user.id)
    await state.reset_state()


@dp.message_handler(lambda m: m.from_user.id in BOT_ADMINS, content_types=['text'], state='ADMIN_BAN')
async def handle_user_for_uban(m: types.Message):
    list = m.text.split(' ')
    if len(list) == 2:
        id = list[0]
        decision = list[1]
        if id.isdigit() and decision.isdigit():
            result = uban_user(id, decision)
            await m.reply(result, reply=False)
            if int(decision) == 0:
                await bot.send_message(id, YOU_WAS_BANNED)
        else:
            await m.reply(NOT_INTEGER, reply=False)
    else:
        await m.reply(LITTLE_VALUE, reply=False)
    state = dp.current_state(user=m.from_user.id)
    await state.reset_state()


@dp.callback_query_handler(lambda c: c.data == 'cancel', state='*')
async def cancel_button_handle(c: types.callback_query):
    await c.message.edit_text(CANCEL_TEXT)

    state = dp.current_state(user=c.from_user.id)
    await state.reset_state()


# TODO разобраться с обработкой кнопки отмены по каналу (мб удаляет его из бд)
@dp.callback_query_handler(lambda c: 'cancel_' in c.data,
                           state=['CONFIRMATION', 'GET_SUB_COUNT', 'SEND_CLIP_COUNT', 'GET_TT_VIDEO'])
async def cancel_button_with_id(c: types.callback_query):
    logger = logging.getLogger(f'{get_logger_name_main()}.{cancel_button_with_id.__name__}')

    clip_id = int(c.data.replace('cancel_', ''))
    user_id = c.from_user.id

    logger.info(f'{user_id} delete order_clip_id {clip_id} from db')

    status = await delete_tt_clip_from_promo_db(clip_id)

    if status:
        logger.info(f'{user_id} clip deleted: {clip_id}')

        await c.message.edit_text(CANCEL_TEXT)
        state = dp.current_state(user=c.from_user.id)
        await state.reset_state()
    else:
        logger.info(f'{user_id} clip not deleted, on promotion: {clip_id}')

        await c.message.edit_text(TT_VIDEO_ON_PROMOTION)
        state = dp.current_state(user=c.from_user.id)
        await state.reset_state()


# TODO доделать если нужно вообще (типа удаляет привязку акка из базы если вдруг юзер не так ввел)
@dp.callback_query_handler(lambda c: 'cancel_tt_acc_' in c.data, state=['REG_TT_ACCOUNT'])
async def cancel_tt_acc_button_handler(c: types.callback_query):
    # logger = logging.getLogger(f'{get_logger_name_main()}.{cancel_tt_acc_button_handler.__name__}')

    # user_id = c.from_user.id
    #
    # logger.info(f'{user_id} delete order_clip_id {clip_id} from db')

    user_id = c.data.replace('cancel_tt_acc_', '')

    # TODO сделать отвязку
    status = delete_tt_account_from_user_db(user_id)

    if status == 0:
        await c.message.edit_text(TT_ACC_ACCEPTED)
        state = dp.current_state(user=c.from_user.id)
        await state.reset_state()
    else:
        await c.message.edit_text(TT_ACC_DELETED)
        state = dp.current_state(user=c.from_user.id)
        await state.reset_state()


@dp.callback_query_handler(lambda c: 'check_payment_' in c.data, state='CONFIRM_TOP_UP_BALANCE')
async def check_payment(c: types.callback_query):
    logger = logging.getLogger(f'{get_logger_name_main()}.{check_payment.__name__}')

    payment_id = int(c.data.replace('check_payment_', ''))
    user_id = c.from_user.id

    logger.info(f'{user_id} try to check_payment with id: {payment_id}')

    try:
        payment = await view_payment(payment_id)
        payment_status = payment[0]
        payment_amount = payment[1]

        logger.info(f'{user_id} - {payment_id} payed {payment_amount} with status {payment_status}')

        # await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)

        if payment_status == 1:
            await c.message.edit_text(MONEY_EARNED)
            await deposit_money_to_balance(user_id, payment_amount)

            state = dp.current_state(user=c.from_user.id)
            await state.reset_state()
        else:
            payment_menu = InlineKeyboardMarkup()
            payment_menu.add(
                InlineKeyboardButton(text='Проверить оплату', callback_data='check_payment_' + str(payment_id)),
                InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel'))

            # TODO запихивать в стейт машину
            top_up_balance_message_id = await bot.send_message(
                user_id, MONEY_NOT_EARNED, reply_markup=payment_menu)

    except Exception as e:
        logger.error(f'{user_id} got ex: {e}')
        await bot.send_message(user_id, 'Произошла ошибка, нажмите кнопку "Отмена"',
                               reply_markup=cancel_menu)


@dp.callback_query_handler(lambda c: 'confirm_' in c.data, state='CONFIRMATION')
async def confirm_clip_promo(c: types.callback_query):
    logger = logging.getLogger(f'{get_logger_name_main()}.{confirm_clip_promo.__name__}')

    order_id = int(c.data.replace('confirm_', ''))
    user_id = c.from_user.id

    logger.info(f'user {user_id} try to confirm order {order_id}')

    try:
        confirm_return = await confirm_clip_update_status(order_id)

        if confirm_return:
            logger.info(f'user {user_id} confirm order {order_id} success')

            await c.message.edit_text(CLIP_SUCCESSFULLY_ADDED)
            state = dp.current_state(user=c.from_user.id)
            await state.reset_state()

            for user_id in await get_all_user_id():
                try:
                    await bot.send_message(user_id, NEW_CLIP_TO_PROMO)
                except BotBlocked:
                    pass
                    # print('User ' + str(user_id) + ' was banned US BOT FUCK! ;(')

        else:
            logger.info(f'user {user_id} confirm order {order_id} failed')

            await c.message.edit_text(CLIP_IS_NOT_PROMO)
            state = dp.current_state(user=user_id)
            await state.reset_state()

    except Exception as e:
        logger.error(f'{user_id} got ex: {e}')
        await bot.send_message(user_id, 'Произошла ошибка, нажмите кнопку "Отмена"',
                               reply_markup=cancel_menu)


@dp.callback_query_handler(lambda c: 'check_clip_' in c.data)
async def check_clip(c: types.CallbackQuery):
    logger = logging.getLogger(f'{get_logger_name_main()}.{check_clip.__name__}')

    clip_order_id = int(c.data.replace('check_clip_', ''))
    user_id = c.from_user.id

    logger.info(f'check_clip user"s {user_id} for paying {clip_order_id}')

    try:
        # TODO добавить проверку музыки по полю из БД
        await check_clip_for_paying(user_id, clip_order_id)
        user_alltime_clips = await get_alltime_clips(user_id)

        state = dp.current_state(user=user_id)

        logger.info(f'user"s clip_order {clip_order_id} success paying added {clip_order_id}')

        # TODO запускать отдельно в другом месте
        paying_task = asyncio.create_task(pay_user_for_tasks(user_id, 150))
        reset_state_task = asyncio.create_task(state.reset_state())
        send_msg_clip_checking_task = asyncio.create_task(c.message.edit_text(TT_CLIP_CHECKING))

        logger.info(f'user {user_id} paying tasks async')
        # сразу запускаем эту таску, чтобы пользователю побыстрее пришли бабки
        payment_sum = await paying_task
        # если клипы засчитались в другую проверку и нет смысла оповещать о 0 бабок
        # (там их несколько подряд можно запустить)
        if payment_sum != 0:
            logger.info(f'user {user_id} update tables for paying')

            user_in_abusers_status = await add_user_to_clip_abusers(clip_order_id, user_id)
            alltime_get_clips_update_status = await update_user_alltime_get_clips(clip_order_id, 1)

            if user_in_abusers_status and alltime_get_clips_update_status:
                logger.info(f'user {user_id} get paying')

                if user_alltime_clips == 0:
                    logger.info(f'user {user_id} pay by referral')

                    ref_father_id = await pay_by_referral(user_id)
                    if ref_father_id:
                        # отправит сообщение реф отцу об успешном выполнении задания его сыном
                        await bot.send_message(ref_father_id, 'Ваш реферал только что выполнил первое задание! '
                                                              'Вы получили ' + str(REF_BONUS) + ' RUB.')
                # отправит сообщение, когда получит ответ о пополнении кошелька
                await bot.send_message(user_id, 'Поздравляю! Вы получили ' + str(payment_sum) + ' RUB.')
            else:
                logger.info(f'user {user_id} not earn money')

        # запускаем такси смены состояния и отправки ответа от бота
        await reset_state_task
        await send_msg_clip_checking_task

    except Exception as e:
        logger.error(f'{user_id} got ex: {e}')
        await bot.send_message(user_id, 'Произошла ошибка, нажмите кнопку "Отмена"',
                               reply_markup=cancel_menu)


# TODO сделать обновление инлайн клавы и видоса при нажатии на кнопку
@dp.callback_query_handler(lambda c: 'skip_' in c.data)
async def skip_clip(c: types.CallbackQuery):
    logger = logging.getLogger(f'{get_logger_name_main()}.{skip_clip.__name__}')

    clip_id = int(c.data.replace('skip_', ''))
    user_id = c.from_user.id

    logger.info(f'user {user_id} try to skip clip {clip_id}')
    logger.info(f'user {user_id} add clip to skipped {clip_id}')

    try:
        await add_video_to_skipped(user_id, clip_id)

        await c.message.edit_text(TT_VIDEO_SKIPPED)

        logger.info(f'user {user_id} get awailable clips')

        clips_info = await get_clips_for_work(user_id)

        if clips_info.get('clips_exist'):
            logger.info(f'user {user_id} clips to work exist')

            await c.message.reply(clips_info.get('reply_msg'),
                                  reply_markup=clips_info.get('inline_kb'),
                                  reply=False)
        else:
            logger.info(f'user {user_id} clips to work NOT exist')

            await c.message.reply(clips_info.get('reply_msg'),
                                  reply=False)

        logger.info(f'user {user_id} start timer to return clip to queue {clip_id} for 1800 sec')
        # таймер на 30 минут для появления видоса в списке на продвижение
        return_clip_in_queue_success = asyncio.create_task(return_clip_int_queue(user_id, clip_id, 1800))
        if await return_clip_in_queue_success:
            # отправит сообщение о появлении нового клипа
            await bot.send_message(user_id, NEW_CLIP_TO_PROMO)

    except Exception as e:
        logger.error(f'{user_id} got ex: {e}')
        await bot.send_message(user_id, 'Произошла ошибка, нажмите кнопку "Отмена"',
                               reply_markup=cancel_menu)


@dp.callback_query_handler(lambda c: c.data == 'stat')
async def admin_stat_button(c: types.CallbackQuery):
    user_id = c.from_user.id

    logger = logging.getLogger(f'{get_logger_name_main()}.{admin_stat_button.__name__}')
    logger.info(f'admin {user_id} get stat')

    await c.message.edit_text(START_COLLECT_STAT)
    users = await get_all_user_id()
    alive_users = 0
    blocked_users = 0
    # TODO сделать бегунок о выполненной работе
    for user in users:
        try:
            await bot.send_chat_action(chat_id=user, action='typing')
            alive_users += 1
        except (BotBlocked, UserDeactivated):
            blocked_users += 1

        await asyncio.sleep(0.1)
    await bot.send_message(c.from_user.id, STATISTICS(alive_users, blocked_users))


@dp.callback_query_handler(lambda c: c.data == 'mail')
async def admin_mail_button(c: types.CallbackQuery):
    user_id = c.from_user.id

    logger = logging.getLogger(f'{get_logger_name_main()}.{admin_mail_button.__name__}')
    logger.info(f'admin {user_id} wanna mailing')

    await c.message.edit_text(SEND_MESSAGE_FOR_SEND, parse_mode='Markdown', reply_markup=cancel_menu)
    state = dp.current_state(user=c.from_user.id)
    await state.set_state('GET_MSG_FOR_MAIL')


@dp.callback_query_handler(lambda c: c.data == 'uban')
async def admin_uban_button(c: types.CallbackQuery):
    user_id = c.from_user.id

    logger = logging.getLogger(f'{get_logger_name_main()}.{admin_uban_button.__name__}')
    logger.info(f'admin {user_id} uban')

    await c.message.edit_text(SEND_USER_FOR_UBAN, reply_markup=cancel_menu)
    state = dp.current_state(user=c.from_user.id)
    await state.set_state('ADMIN_BAN')


# админская функция вывода средст пользователем
@dp.callback_query_handler(lambda c: c.data == 'admin_withdraw')
async def get_unverified_tasks(c: types.CallbackQuery):
    admin_user_id = c.from_user.id

    logger = logging.getLogger(f'{get_logger_name_main()}.{get_unverified_tasks.__name__}')
    logger.info(f'admin {admin_user_id} try to admin_withdraw')

    # TODO выдирать из таблицы и выводить которые еще не проверены
    await c.message.edit_text(ADMIN_WITHDRAW)

    logger.info(f'admin {admin_user_id} get first unverified withdraw funds')
    # забираем инфу о последних неоплаченных выводах средст
    first_unverified_withdraw_funds = await get_first_unverified_withdraw_funds()

    if first_unverified_withdraw_funds:
        logger.info(f'admin {admin_user_id} first withdraw funds got, get data')

        withdraw_funds_dict = list(first_unverified_withdraw_funds.values())[0]

        user_id = withdraw_funds_dict['user_id']

        logger.info(f'admin {admin_user_id} data got, get referrals_count')
        # добавляем количество рефералов пользователя в словарь
        user_ref_count = await get_referrals_count(user_id)
        withdraw_funds_dict['user_ref_count'] = user_ref_count

        logger.info(f'admin {admin_user_id} got referrals_count, get alltime_clips')
        # добавляем количество снятых пользователем видосов в словарь
        user_alltime_clips = await get_alltime_clips(user_id)
        withdraw_funds_dict['user_alltime_clips'] = user_alltime_clips

        withdraw_id_list_str = ''
        for withdraw_id in withdraw_funds_dict['withdraw_id_list']:
            withdraw_id_list_str += str(withdraw_id) + '_'

        logger.info(f'admin {admin_user_id} got all')

        withdraw_keyboard = InlineKeyboardMarkup()
        # TODO доделать кнопки
        withdraw_keyboard.add(
            InlineKeyboardButton(text='Деньги выведены', callback_data='admin_withdraw_' + withdraw_id_list_str))

        await c.message.reply(ADMIN_WITHDRAW_LIST(withdraw_funds_dict), reply=False, parse_mode='HTML',
                              reply_markup=withdraw_keyboard)
    else:
        logger.info(f'admin {admin_user_id} withdraw funds list is empty')

        await c.message.reply('Список пустует диз, побереги бабки)', reply=False, parse_mode='HTML')

    state = dp.current_state(user=c.from_user.id)
    await state.reset_state()


# TODO дописать пополнение
@dp.callback_query_handler(lambda c: c.data == 'top_up_balance')
async def top_up_balance(c: types.CallbackQuery):
    logger = logging.getLogger(f'{get_logger_name_main()}.{top_up_balance.__name__}')

    user_id = c.from_user.id
    logger.info(f'user {user_id} wanna top up balance')

    state = dp.current_state(user=c.from_user.id)
    await state.set_state('TOP_UP_BALANCE')

    await c.message.reply(TOP_UP_BALANCE, reply=False, parse_mode='HTML', reply_markup=cancel_menu)
    # await c.message.edit_text(TOP_UP_BALANCE, reply_markup=cancel_menu)


# TODO дописать пополнение
@dp.callback_query_handler(lambda c: c.data == 'withdraw_funds')
async def withdraw_funds(c: types.CallbackQuery):
    logger = logging.getLogger(f'{get_logger_name_main()}.{withdraw_funds.__name__}')

    user_id = c.from_user.id
    logger.info(f'user {user_id} wanna withdraw_funds')

    try:
        balance = await get_user_balance_tt(user_id=user_id)

        if balance >= 200:
            await c.message.reply(WITHDRAW_FUNDS(balance), reply=False, parse_mode='HTML', reply_markup=cancel_menu)

            state = dp.current_state(user=user_id)
            await state.set_state('WITHDRAW_FUNDS_VALIDATION')
        else:
            await c.message.reply(WITHDRAW_FUNDS_NOT_ENOUGH(balance), reply=False, parse_mode='HTML')
            state = dp.current_state(user=user_id)
            await state.reset_state()

    except Exception as e:
        logger.error(f'{user_id} got ex: {e}')
        await bot.send_message(user_id, 'Произошла ошибка, нажмите кнопку "Отмена"',
                               reply_markup=cancel_menu)


@dp.callback_query_handler(lambda c: 'withdraw_funds_' in c.data, state='WITHDRAW_FUNDS_WAIT_MONEY')
async def withdraw_funds_wait_money(c: types.CallbackQuery):
    logger = logging.getLogger(f'{get_logger_name_main()}.{withdraw_funds_wait_money.__name__}')

    user_id = c.from_user.id
    withdraw_id = int(c.data.replace('withdraw_funds_', ''))
    logger.info(f'user {user_id} wanna withdraw_funds, withdraw_id = {withdraw_id}')

    try:
        funds_amount = await update_withdraw_status(withdraw_id, 2)

        user_id = c.from_user.id
        current_user_balance = await get_user_balance_tt(user_id)
        new_user_balance = current_user_balance - funds_amount
        await change_balance_tt(user_id, new_user_balance)

        logger.info(f'user"s {user_id} balance changed to {new_user_balance}')

        state = dp.current_state(user=user_id)
        await state.reset_state()

        await c.message.edit_text(WITHDRAW_FUNDS_WAIT_MONEY)

    except Exception as e:
        logger.error(f'{user_id} got ex: {e}')
        await bot.send_message(user_id, 'Произошла ошибка, нажмите кнопку "Отмена"',
                               reply_markup=cancel_menu)


@dp.callback_query_handler(lambda c: 'admin_withdraw_' in c.data)
async def admin_withdraw_button(c: types.CallbackQuery):
    user_id = c.from_user.id

    withdraw_id_list = c.data.replace('admin_withdraw_', '')
    converted_withdraw_id_list = withdraw_id_list.split('_')

    logger = logging.getLogger(f'{get_logger_name_main()}.{admin_withdraw_button.__name__}')
    logger.info(f'admin {user_id} wanna submit some withdraws: {withdraw_id_list}')

    try:
        for withdraw_id in converted_withdraw_id_list:
            if withdraw_id != '':
                await submit_withdraw(int(withdraw_id))

        logger.info(f'admin {user_id} success submit all withdraws')

        state = dp.current_state(user=user_id)
        await state.reset_state()

        await c.message.edit_text(ADMIN_WITHDRAW_FUNDS_SUCCESS)

    except Exception as e:
        logger.error(f'{user_id} got ex: {e}')
        await bot.send_message(user_id, 'Произошла ошибка, нажмите кнопку "Отмена"',
                               reply_markup=cancel_menu)


@dp.callback_query_handler(lambda c: c.data == 'chb')
async def change_balance_button(c: types.CallbackQuery):
    logger = logging.getLogger(f'{get_logger_name_main()}.{change_balance_button.__name__}')
    logger.info(f'admin {c.from_user.id} change wanna balance some user')

    state = dp.current_state(user=c.from_user.id)
    await state.set_state('ADMIN_CHANGE_BALANCE')

    await c.message.edit_text(SEND_USER_FOR_CHANGE_BALANCE)

# админская функция выгруза всех данных из базы
@dp.callback_query_handler(lambda c: c.data == 'admin_get_db_data')
async def admin_get_db_data(c: types.CallbackQuery):
    logger = logging.getLogger(f'{get_logger_name_main()}.{admin_get_db_data.__name__}')
    logger.info(f'admin {c.from_user.id} get db_data')

    await c.message.edit_text(ADMIN_GET_DB_DATA)

    excel_file_name = 'db/db_data.xlsx'

    await save_data_into_excel(excel_file_name)

    excel_file = open(excel_file_name, 'rb')
    await bot.send_document(chat_id=c.from_user.id, document=excel_file)

    state = dp.current_state(user=c.from_user.id)
    await state.reset_state()


# админская функция выгрузки логов с сервака в файлик в телегу
@dp.callback_query_handler(lambda c: c.data == 'admin_get_logs')
async def admin_get_logs(c: types.CallbackQuery):
    user_id = c.from_user.id

    logger = logging.getLogger(f'{get_logger_name_main()}.{admin_get_logs.__name__}')
    logger.info(f'admin {user_id} get logs')

    await c.message.edit_text(ADMIN_GET_LOGS)

    logs_file_name = 'main.log'

    logs_file_bytes = open(logs_file_name, 'rb')
    await bot.send_document(chat_id=user_id, document=logs_file_bytes)

    state = dp.current_state(user=user_id)
    await state.reset_state()


async def on_shutdown(dispatcher: Dispatcher):
    logger = logging.getLogger(f'{get_logger_name_main()}.{on_shutdown.__name__}')
    logger.info(f'close, wait_closed bot')

    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_shutdown=on_shutdown, loop=loop)
