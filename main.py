import random
import time

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.utils import executor
from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.helper import Helper, ListItem

from payment.qiwi.payment import *
from utility.messages import *
from utility.validation import *

loop = asyncio.get_event_loop()

bot = Bot(token=BOT_TOKEN, loop=loop)

dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())


# TODO придумать че делать со стейтами
class UserStates(Helper):
    GET_CHANNEL_TO_UP = ListItem()
    GET_SUB_COUNT = ListItem()
    CONFIRMATION = ListItem()
    GET_MSG_FOR_MAIL = ListItem()
    GET_USER_FOR_UBAN = ListItem()
    GET_USER_FOR_CHB = ListItem()


main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add('Заработать', 'Заказать')
main_menu.add('👤 Профиль', 'Партнёрская программа')

admin_menu = InlineKeyboardMarkup()

statistics_bt = InlineKeyboardButton(text='📊 Статистика', callback_data='stat')
mail_bt = InlineKeyboardButton(text='✉️ Рассылка', callback_data='mail')
give_uban_bt = InlineKeyboardButton(text='🚷 Выдать бан/разбан', callback_data='uban')
change_balance_bt = InlineKeyboardButton(text='💳 Изменить баланс', callback_data='chb')
unverified_tasks = InlineKeyboardButton(text='Вывести деньги пользователю', callback_data='admin_withdraw')

admin_menu.add(statistics_bt, mail_bt)
admin_menu.add(give_uban_bt, change_balance_bt)
admin_menu.add(unverified_tasks)

cancel_menu = InlineKeyboardMarkup()
cancel_bt = InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel')
cancel_menu.add(cancel_bt)


# TODO Доделать таймер
def update_tt_usernames(time_interval):
    while True:
        print('Doing timer work')
        update_tt_acc_username_all()
        time.sleep(time_interval)


async def pay_user_for_tasks(user_id, delay):
    await asyncio.sleep(delay)
    # TODO сделать логирование вместо вот этого
    print('Paying completed tasks for user: ' + str(user_id))
    payment_sum = await pay_all_completed_user_tasks(user_id)

    return payment_sum


# TODO Доделать таймер
async def return_clip_int_queue(user_id, clip_id, delay):
    await asyncio.sleep(delay)
    # TODO добавить логирование
    print('Wait for clip in queue for : ' + str(delay) + ', clip_id = ' + str(clip_id))
    await is_return_clip_in_queue(user_id, clip_id)

    return True


@dp.message_handler(commands=['start'])
async def start_commands_handle(m: types.Message):
    state = dp.current_state(user=m.from_user.id)
    await state.reset_state()

    if await is_user_in_db_tt(m.from_user.id) < 1:
        argument = m.get_args()
        if (argument is not None) and (argument.isdigit() is True) and (await is_user_in_db_tt(argument)) == 1:
            await add_user_to_db_tt(m.from_user.id, ref_father=argument)

            await m.reply(START, reply=False, parse_mode='HTML', reply_markup=main_menu)
            await bot.send_message(text=NEW_REFERRAL(argument), chat_id=argument)
        else:
            await add_user_to_db_tt(m.from_user.id)
            await m.reply(START, reply=False, parse_mode='HTML', reply_markup=main_menu)
    else:
        await m.reply(UPDATE, reply=False, parse_mode='HTML', reply_markup=main_menu)


@dp.message_handler(commands=['help'])
async def start_commands_handle(m: types.Message):
    state = dp.current_state(user=m.from_user.id)
    await state.reset_state()

    await m.reply(HELP, reply=False, parse_mode='HTML', reply_markup=main_menu)


@dp.message_handler(lambda m: m.from_user.id in BOT_ADMINS, commands=['admin'])
async def admin_command_handle(m: types.Message):
    await m.reply(SELECT_ADMIN_MENU_BUTTON, reply=False, reply_markup=admin_menu)


@dp.message_handler(lambda m: m.from_user.id not in BOT_ADMINS, commands=['admin'])
async def handle_not_admin(m: types.Message):
    await m.reply(YOU_WAS_HACK_ME, reply=False)


@dp.message_handler(lambda m: m.text == '👤 Профиль')
async def profile_button_handle(m: types.Message):
    top_up_balance = InlineKeyboardMarkup()
    top_up_balance.add(
        InlineKeyboardButton(text='Пополнить баланс', callback_data='top_up_balance'),
        InlineKeyboardButton(text='Вывести средства', callback_data='withdraw_funds'))

    await m.reply(await PROFILE(m), reply=False, parse_mode='HTML', reply_markup=top_up_balance)


@dp.message_handler(lambda m: m.text == 'Заказать')
async def add_tt_video_handle(m: types.Message):
    state = dp.current_state(user=m.from_user.id)
    await state.set_state('GET_TT_VIDEO')
    await m.reply(GIVE_TT_VIDEO_LINK, reply=False, parse_mode='HTML', reply_markup=cancel_menu)


@dp.message_handler(content_types=['text'], state='GET_TT_VIDEO')
async def tt_video_handle(m: types.Message):
    try:
        if m.content_type == 'text':
            clip_link = m.text

            if valid_tt_link(clip_link):
                # TODO заглушка
                # tt_clip_data = get_music_id_from_clip_tt(clip_link)
                # tt_clip_id = clip_data.get('clip_id')
                # tt_music_id = clip_data.get('music_id')

                tt_clip_id = 1
                tt_music_id = 2

                # TODO сохранять видос/линк на него в БД
                order_id = await save_tt_clip(client=m.from_user.id, clip_link=clip_link,
                                              clip_id=tt_clip_id, music_id=tt_music_id)

                cancel_promotion = InlineKeyboardMarkup()
                # TODO добавить эту штуку для удаления видоса в случае нажатия кнопки отмена
                cancel_promotion.add(
                    # TODO изменить clip_id в str(0)
                    InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_' + str(order_id)))

                await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)
                await m.reply(SEND_CLIP_COUNT(m.from_user.id, clip_link), reply=False, parse_mode='HTML',
                              reply_markup=cancel_promotion)

                state = dp.current_state(user=m.from_user.id)

                # TODO поменять статус и начать пиар видео
                await state.set_state('SEND_CLIP_COUNT')
            else:
                cancel = InlineKeyboardMarkup()
                cancel.add(
                    InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel'))

                await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)
                await m.reply(WRONG_TT_CLIP_LINK, reply=False, parse_mode='HTML',
                              reply_markup=cancel)

        else:
            await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)

            cancel_promotion = InlineKeyboardMarkup()
            # TODO сделать обработку этой кнопки отмены
            cancel_promotion.add(
                InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel'))

            # TODO Добраотка
            await m.reply(TT_LINK_VIDEO_ERR(), reply=False, parse_mode='HTML',
                          reply_markup=cancel_menu)

    except Exception as e:
        await m.reply(e, reply_markup=cancel_menu)


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


@dp.message_handler(lambda m: m.text == 'Заработать')
async def sent_instruction_for_get_money(m: types.Message):
    user_id = m.from_user.id

    if await tt_acc_not_exist(user_id):
        state = dp.current_state(user=user_id)
        await state.set_state('REG_TT_ACCOUNT')
        await m.reply(TT_ACCOUNT, reply=False, parse_mode='HTML', reply_markup=cancel_menu)
    else:
        # стейт мешает потом опять зайти в эту функцию
        # state = dp.current_state(user=user_id)
        # await state.set_state('GET_MONEY')

        clips_info = await get_money(user_id)

        if clips_info.get('clips_exist'):
            await m.reply(clips_info.get('reply_msg'),
                          reply_markup=clips_info.get('inline_kb'),
                          reply=False)
        else:
            await m.reply(clips_info.get('reply_msg'),
                          reply=False)

        # try:
        #
        # except Exception as e:
        #     pass
        #     # TODO понять из за чего это все
        #     # print('Exc via reply clip list to user:\n' + str(e))


async def get_money(user_id):
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
async def tt_account_reg(m: types.Message):
    try:
        if m.content_type == 'text':
            tt_acc_link = m.text

            # TODO доделать парсер аккаута
            if check_tt_account_link(tt_acc_link):
                # TODO сохранять ссылку на акк в БД юзера
                user_id = m.from_user.id
                return_tt_acc = await add_tt_acc_to_user(user_id, tt_acc_link)

                # cancel_promotion = InlineKeyboardMarkup()
                # TODO добавить эту штуку для отвязки акка в случае нажатия кнопки отмена
                # cancel_promotion.add(
                #     InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_tt_acc_' + str(user_id)))

                await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)
                await m.reply(TT_ACC_ACCEPTED, reply=False, parse_mode='HTML')
                # reply_markup=cancel_promotion)
            else:
                await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)
                await m.reply(TT_ACC_WRONG, reply=False, parse_mode='HTML')

            state = dp.current_state(user=m.from_user.id)
            await state.reset_state()
        else:
            await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)

            cancel_promotion = InlineKeyboardMarkup()
            # TODO сделать обработку этой кнопки отмены
            cancel_promotion.add(
                InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel'))

            # TODO Добраотка
            await m.reply(TT_LINK_ACC_ERR(), reply=False, parse_mode='HTML',
                          reply_markup=cancel_menu)

    except Exception as e:
        await m.reply(e, reply_markup=cancel_menu)


# TODO доделать покупку клипов
@dp.message_handler(state='SEND_CLIP_COUNT')
async def handle_send_clip_count(m: types.Message):
    if (m.content_type == 'text') and (m.text.isdigit() is True) and (
            int(m.text) >= 1) and await get_user_balance_tt(m.from_user.id) >= int(m.text) * CASH_MIN:

        video_to_promo_count = int(m.text)
        order_id = await update_tt_video_goal(video_to_promo_count)

        confirmation_menu = InlineKeyboardMarkup()
        confirmation_menu.add(
            InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_' + str(order_id)),
            InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm_' + str(order_id)))

        state = dp.current_state(user=m.from_user.id)
        await state.set_state('CONFIRMATION')

        await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)

        # TODO выводить ссылку на видос
        await m.reply(
            CONFIRM_ADDING_VIDEO_TO_PROMO(video_to_promo_count, video_to_promo_count * CASH_MIN),
            reply=False,
            reply_markup=confirmation_menu)
    else:
        order_id = await get_video_stat(m.from_user.id)

        # TODO убрать кнопку и удалять видос из базы или ставить статус говна
        cancel_pay_menu = InlineKeyboardMarkup()
        cancel_pay_menu.add(
            InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_' + str(order_id)))

        await m.reply(INSUFFICIENT_FUNDS, reply=False, reply_markup=cancel_pay_menu)


# пополнение баланса
@dp.message_handler(content_types=types.ContentType.ANY, state='TOP_UP_BALANCE')
async def top_up_balance(m: types.Message):
    user_id = m.from_user.id
    bot_last_message_id = m.message_id - 1

    if m.content_type == 'text':
        money_amount = int(m.text)

        payment_info = await add_user_payment(user_id, money_amount)
        payment_comment = payment_info[0]
        payment_id = payment_info[1]

        # TODO придумать че делать, когда отправляется список объектов
        await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
        # await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)

        payment_menu = InlineKeyboardMarkup()
        payment_menu.add(
            InlineKeyboardButton(text='Проверить оплату', callback_data='check_payment_' + str(payment_id)),
            InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel'))

        await m.reply(
            MONEYS(money_amount, payment_comment),
            reply=False, reply_markup=payment_menu, parse_mode='HTML')
    else:
        await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)

        await m.reply(WRONG_MONEY_AMOUNT, reply=False, reply_markup=cancel_menu)


# проверка данных для вывода средств
@dp.message_handler(content_types=types.ContentType.ANY, state='WITHDRAW_FUNDS_VALIDATION')
async def withdraw_funds_validation(m: types.Message):
    user_id = m.from_user.id
    bot_last_message_id = m.message_id - 1

    if m.content_type == 'text':
        funds_amount = m.text

        try:
            funds_amount = int(funds_amount)
            balance = await get_user_balance_tt(user_id=user_id)

            if balance >= funds_amount:
                if funds_amount >= 200:
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
                    await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
                    await m.reply(WITHDRAW_SUM_LESS_200, reply=False, reply_markup=cancel_menu)
            else:
                await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
                await m.reply(INSUFFICIENT_FUNDS_TO_WITHDRAW, reply=False, reply_markup=cancel_menu)

        except ValueError:
            await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
            await m.reply(WRONG_WITHDRAW_FUNDS, reply=False, reply_markup=cancel_menu)
    else:
        await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
        await m.reply(WRONG_WITHDRAW_FUNDS, reply=False, reply_markup=cancel_menu)


# выбор способа вывода средств
@dp.message_handler(content_types=types.ContentType.ANY, state='WITHDRAW_FUNDS_LOCATION')
async def withdraw_funds_location(m: types.Message):
    user_id = m.from_user.id
    bot_last_message_id = m.message_id - 1

    if m.content_type == 'text':
        withdraw_funds_number = m.text

        withdraw_number_validation = valid_withdraw_number(withdraw_funds_number)

        if withdraw_number_validation[0]:
            last_withdraw_id = await get_last_withdraw()

            await update_withdraw_location(last_withdraw_id, withdraw_number_validation[1],
                                           withdraw_funds_number)

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
            pass
    else:
        await bot.edit_message_reply_markup(chat_id=user_id, message_id=bot_last_message_id)
        await m.reply(WRONG_WITHDRAW_FUNDS_LOCATION, reply=False, reply_markup=cancel_menu)


# админская способность рассылки
@dp.message_handler(content_types=['text', 'video', 'photo', 'document', 'animation'], state='GET_MSG_FOR_MAIL')
async def send_mail(m: types.Message):
    state = dp.current_state(user=m.from_user.id)
    await state.reset_state()
    users = get_users_for_mailing()
    if m.content_type == 'text':
        all_users = 0
        blocked_users = 0
        for x in users:
            try:
                await bot.send_message(x[0], m.html_text, parse_mode='HTML')
                all_users += 1
                await asyncio.sleep(0.3)
            except BotBlocked:
                blocked_users += 1
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


@dp.message_handler(lambda m: m.text == 'Партнёрская программа')
async def referal_button_handle(m: types.Message):
    get_bot = await bot.get_me()
    await m.reply(PARTNER_PROGRAM(get_bot.username, m.from_user.id,
                                  await get_referrals_count(m.from_user.id)),
                  reply=False, parse_mode='HTML')


@dp.message_handler(lambda m: m.from_user.id in BOT_ADMINS, content_types=['text'], state='GET_USER_FOR_CHB')
async def handle_user_for_chb(m: types.Message):
    change_balance_request = m.text.split(' ')

    if len(change_balance_request) == 2:
        user_id = change_balance_request[0]
        balance_increase = change_balance_request[1]

        if user_id.isdigit() and balance_increase.lstrip('-').isdigit():

            increase_balance_result = await increase_balance_tt(user_id, balance_increase)

            await m.reply(increase_balance_result, reply=False)
        else:
            await m.reply(NOT_INTEGER, reply=False)
    else:
        await m.reply(LITTLE_VALUE, reply=False)

    state = dp.current_state(user=m.from_user.id)
    await state.reset_state()


@dp.message_handler(lambda m: m.from_user.id in BOT_ADMINS, content_types=['text'], state='GET_USER_FOR_UBAN')
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
async def cancel_wnum_button_handler(c: types.callback_query):
    clip_id = int(c.data.replace('cancel_', ''))

    status = await delete_tt_clip_from_promo_db(clip_id)

    if status:
        await c.message.edit_text(CANCEL_TEXT)
        state = dp.current_state(user=c.from_user.id)
        await state.reset_state()
    else:
        await c.message.edit_text(TT_VIDEO_ON_PROMOTION)
        state = dp.current_state(user=c.from_user.id)
        await state.reset_state()


@dp.callback_query_handler(lambda c: 'cancel_tt_acc_' in c.data, state=['REG_TT_ACCOUNT'])
async def cancel_tt_acc_button_handler(c: types.callback_query):
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


@dp.callback_query_handler(lambda c: 'check_payment_' in c.data, state='TOP_UP_BALANCE')
async def confirm_button_handler(c: types.callback_query):
    payment_id = int(c.data.replace('check_payment_', ''))
    user_id = c.from_user.id

    payment = await view_payment(payment_id)
    payment_status = payment[0]
    payment_amount = payment[1]

    print('user ' + str(user_id) + ' - ' + str(payment_id) + ': payed ' + str(payment_amount) +
          ' with status ' + str(payment_status))

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

        await bot.send_message(user_id, MONEY_NOT_EARNED, reply_markup=payment_menu)


@dp.callback_query_handler(lambda c: 'confirm_' in c.data, state='CONFIRMATION')
async def confirm_button_handler(c: types.callback_query):
    order_id = int(c.data.replace('confirm_', ''))

    confirm_return = await confirm_clip_promo(order_id)

    if confirm_return:
        await c.message.edit_text(CLIP_SUCCESSFULLY_ADDED)
        state = dp.current_state(user=c.from_user.id)
        await state.reset_state()

        for user_id in await get_all_user_id():
            await bot.send_message(user_id, NEW_CLIP_TO_PROMO)
    else:
        await c.message.edit_text(CLIP_IS_NOT_PROMO)
        state = dp.current_state(user=c.from_user.id)
        await state.reset_state()


@dp.callback_query_handler(lambda c: 'check_clip_' in c.data)
async def check_clip(c: types.CallbackQuery):
    clip_order_id = int(c.data.replace('check_clip_', ''))
    user_id = c.from_user.id

    # TODO добавить проверку музыки по полю из БД
    await check_clip_for_paying(user_id, clip_order_id)
    user_alltime_clips = await get_alltime_clips(user_id)

    state = dp.current_state(user=user_id)

    # TODO запускать отдельно в другом месте
    paying_task = asyncio.create_task(pay_user_for_tasks(user_id, 120))
    reset_state_task = asyncio.create_task(state.reset_state())
    send_msg_clip_checking_task = asyncio.create_task(c.message.edit_text(TT_CLIP_CHECKING))

    # сразу запускаем эту таску, чтобы пользователю побыстрее пришли бабки
    payment_sum = await paying_task
    # если клипы засчитались в другую проверку и нет смысла оповещать о 0 бабок
    # (там их несколько подряд можно запустить)
    if payment_sum != 0:
        user_in_abusers_status = await add_user_to_clip_abusers(clip_order_id, user_id)
        alltime_get_clips_update_status = await update_user_alltime_get_clips(clip_order_id, 1)

        if user_in_abusers_status and alltime_get_clips_update_status:

            if user_alltime_clips == 0:
                ref_father_id = await pay_by_referral(user_id)
                if ref_father_id:
                    # отправит сообщение реф отцу об успешном выполнении задания его сыном
                    await bot.send_message(ref_father_id, 'Ваш реферал только что выполнил первое задание! '
                                                          'Вы получили ' + str(REF_BONUS) + ' RUB.')
            # отправит сообщение, когда получит ответ о пополнении кошелька
            await bot.send_message(user_id, 'Поздравляю! Вы получили ' + str(payment_sum) + ' RUB.')
        else:
            print('чув ничего не получил, хотя пытался')

    # запускаем такси смены состояния и отправки ответа от бота
    await reset_state_task
    await send_msg_clip_checking_task


# TODO сделать обновление инлайн клавы и видоса при нажатии на кнопку
@dp.callback_query_handler(lambda c: 'skip_' in c.data)
async def skip_video(c: types.CallbackQuery):
    clip_id = int(c.data.replace('skip_', ''))
    user_id = c.from_user.id

    await add_video_to_skipped(user_id, clip_id)

    await c.message.edit_text(TT_VIDEO_SKIPPED)

    clips_info = await get_money(user_id)

    if clips_info.get('clips_exist'):
        await c.message.reply(clips_info.get('reply_msg'),
                              reply_markup=clips_info.get('inline_kb'),
                              reply=False)
    else:
        await c.message.reply(clips_info.get('reply_msg'),
                              reply=False)

    # таймер на 30 минут для появления видоса в списке на продвижение
    return_clip_in_queue_success = asyncio.create_task(return_clip_int_queue(user_id, clip_id, 1800))
    if await return_clip_in_queue_success:
        # отправит сообщение о появлении нового клипа
        await bot.send_message(user_id, NEW_CLIP_TO_PROMO)


@dp.callback_query_handler(lambda c: c.data == 'stat')
async def handle_stat_button(c: types.CallbackQuery):
    await c.message.edit_text(START_COLLECT_STAT)
    users = get_users_for_mailing()
    all_users = 0
    blocked_users = 0
    for x in users:
        try:
            await bot.send_chat_action(chat_id=x[0], action='typing')
            all_users += 1
        except BotBlocked:
            blocked_users += 1

        await asyncio.sleep(0.1)
    await bot.send_message(c.from_user.id, STATISTICS(all_users, blocked_users))


@dp.callback_query_handler(lambda c: c.data == 'mail')
async def handle_mail_button(c: types.CallbackQuery):
    await c.message.edit_text(SEND_MESSAGE_FOR_SEND, parse_mode='Markdown', reply_markup=cancel_menu)
    state = dp.current_state(user=c.from_user.id)
    await state.set_state('GET_MSG_FOR_MAIL')


@dp.callback_query_handler(lambda c: c.data == 'uban')
async def handle_uban_button(c: types.CallbackQuery):
    await c.message.edit_text(SEND_USER_FOR_UBAN, reply_markup=cancel_menu)
    state = dp.current_state(user=c.from_user.id)
    await state.set_state('GET_USER_FOR_UBAN')


# админская функция вывода средст пользователем
@dp.callback_query_handler(lambda c: c.data == 'admin_withdraw')
async def get_unverified_tasks(c: types.CallbackQuery):
    # TODO выдирать из таблицы и выводить которые еще не проверены
    await c.message.edit_text(ADMIN_WITHDRAW)

    # забираем инфу о последних неоплаченных выводах средст
    first_unverified_withdraw_funds = await get_first_unverified_withdraw_funds()

    if first_unverified_withdraw_funds:
        withdraw_funds_dict = list(first_unverified_withdraw_funds.values())[0]

        user_id = withdraw_funds_dict['user_id']
        # добавляем количество рефералов пользователя в словарь
        user_ref_count = await get_referrals_count(user_id)
        withdraw_funds_dict['user_ref_count'] = user_ref_count

        # добавляем количество снятых пользователем видосов в словарь
        user_alltime_clips = await get_alltime_clips(user_id)
        withdraw_funds_dict['user_alltime_clips'] = user_alltime_clips

        withdraw_id_list_str = ''
        for withdraw_id in withdraw_funds_dict['withdraw_id_list']:
            withdraw_id_list_str += str(withdraw_id) + '_'

        withdraw_keyboard = InlineKeyboardMarkup()
        # TODO доделать кнопки
        withdraw_keyboard.add(
            InlineKeyboardButton(text='Деньги выведены', callback_data='admin_withdraw_' + withdraw_id_list_str))

        await c.message.reply(ADMIN_WITHDRAW_LIST(withdraw_funds_dict), reply=False, parse_mode='HTML',
                              reply_markup=withdraw_keyboard)
    else:
        await c.message.reply('Список пустует диз, побереги бабки)', reply=False, parse_mode='HTML')

    state = dp.current_state(user=c.from_user.id)
    await state.reset_state()


# TODO дописать пополнение
@dp.callback_query_handler(lambda c: c.data == 'top_up_balance')
async def handle_uban_button(c: types.CallbackQuery):
    await c.message.reply(TOP_UP_BALANCE, reply=False, parse_mode='HTML', reply_markup=cancel_menu)
    # await c.message.edit_text(TOP_UP_BALANCE, reply_markup=cancel_menu)
    state = dp.current_state(user=c.from_user.id)
    await state.set_state('TOP_UP_BALANCE')


# TODO дописать пополнение
@dp.callback_query_handler(lambda c: c.data == 'withdraw_funds')
async def handle_uban_button(c: types.CallbackQuery):
    user_id = c.from_user.id
    balance = await get_user_balance_tt(user_id=user_id)

    if balance >= 200:
        await c.message.reply(WITHDRAW_FUNDS(balance), reply=False, parse_mode='HTML', reply_markup=cancel_menu)

        state = dp.current_state(user=user_id)
        await state.set_state('WITHDRAW_FUNDS_VALIDATION')
    else:
        await c.message.reply(WITHDRAW_FUNDS_NOT_ENOUGH(balance), reply=False, parse_mode='HTML')
        state = dp.current_state(user=user_id)
        await state.reset_state()


@dp.callback_query_handler(lambda c: 'withdraw_funds_' in c.data, state='WITHDRAW_FUNDS_WAIT_MONEY')
async def withdraw_funds(c: types.CallbackQuery):
    withdraw_id = c.data.replace('withdraw_funds_', '')

    funds_amount = await update_withdraw_status(withdraw_id, 2)

    user_id = c.from_user.id
    current_user_balance = await get_user_balance_tt(user_id)
    new_user_balance = current_user_balance - funds_amount
    await change_balance_tt(user_id, new_user_balance)

    state = dp.current_state(user=user_id)
    await state.reset_state()

    await c.message.edit_text(WITHDRAW_FUNDS_WAIT_MONEY)


@dp.callback_query_handler(lambda c: 'admin_withdraw_' in c.data)
async def handle_admin_withdraw_button(c: types.CallbackQuery):
    withdraw_id_list = c.data.replace('admin_withdraw_', '')
    converted_withdraw_id_list = withdraw_id_list.split('_')

    for withdraw_id in converted_withdraw_id_list:
        if withdraw_id != '':
            submit_withdraw(withdraw_id)

    user_id = c.from_user.id

    state = dp.current_state(user=user_id)
    await state.reset_state()

    await c.message.edit_text(ADMIN_WITHDRAW_FUNDS_SUCCESS)


@dp.callback_query_handler(lambda c: c.data == 'chb')
async def handle_chb_button(c: types.CallbackQuery):
    await c.message.edit_text(SEND_USER_FOR_CHANGE_BALANCE)
    state = dp.current_state(user=c.from_user.id)
    await state.set_state('GET_USER_FOR_CHB')


async def on_shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_shutdown=on_shutdown, loop=loop)
