from settings import *
from messages import *
from functions import *
from functions_2_tt import *
import random
import urllib.parse as url_parser
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.utils.exceptions import BotBlocked
import asyncio
from aiogram.utils.exceptions import Unauthorized

loop = asyncio.get_event_loop()

bot = Bot(token=token, loop=loop)

dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())


class UserStates(Helper):
    GET_CHANNEL_TO_UP = ListItem()
    GET_SUB_COUNT = ListItem()
    CONFIRMATION = ListItem()
    GET_MSG_FOR_MAIL = ListItem()
    GET_USER_FOR_UBAN = ListItem()
    GET_USER_FOR_CHB = ListItem()


main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add('Заработать', 'Заказать')
main_menu.add('👤 Профиль')

admin_menu = InlineKeyboardMarkup()
statistics_bt = InlineKeyboardButton(text='📊 Статистика', callback_data='stat')
mail_bt = InlineKeyboardButton(text='✉️ Рассылка', callback_data='mail')
give_uban_bt = InlineKeyboardButton(text='🚷 Выдать бан/разбан', callback_data='uban')
change_balance_bt = InlineKeyboardButton(text='💳 Изменить баланс', callback_data='chb')
admin_menu.add(statistics_bt, mail_bt)
admin_menu.add(give_uban_bt, change_balance_bt)

cancel_menu = InlineKeyboardMarkup()
cancel_bt = InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel')
cancel_menu.add(cancel_bt)


# ==============
async def user_in_channel_checker():
    last_check = get_last_check()
    if last_check == None and count_of_channels() >= 1:
        global check_user_in_ch

        async def check_user_in_ch():
            channels = get_channels_for_check()
            for x in channels:

                my_id = await bot.get_me()
                try:
                    status_bot_in_channel = await bot.get_chat_member(chat_id=x[1], user_id=my_id.id)
                    status_bot_in_channel = status_bot_in_channel.status
                except (Unauthorized, BotBlocked):
                    status_bot_in_channel = 'left'
                if status_bot_in_channel == 'administrator':
                    subs = x[2]
                    checked_users = eval(x[-1])

                    for user in subs:
                        if user not in checked_users:

                            get_user = await bot.get_chat_member(chat_id=x[1], user_id=user)
                            time_from_subs = x[2][user]
                            if get_user.status == 'left' and ((
                                                                      time_from_subs - datetime.datetime.now()).days < SUBSCRIPTION_TERM) and user_was_fine(
                                x[0], user) == False:
                                add_user_to_fined(x[0], user)
                                change_balance(user, FINE_FOR_UNSUBSCRIBING)
                                increase_fine_count(user)
                                username = await bot.get_chat(chat_id=x[1])
                                await bot.send_message(user,
                                                       SUBSCRIPTION_VIOLATION(username.username, SUBSCRIPTION_TERM,
                                                                              FINE_FOR_UNSUBSCRIBING))

                            elif get_user.status == 'left' and ((
                                                                        time_from_subs - datetime.datetime.now()).days >= SUBSCRIPTION_TERM) and user_was_fine(
                                x[0], user) == False:

                                add_member_to_checked(x[0], user)
                else:

                    writer = edit_promotion_status(x[0], 0)
                    id = x[1]
                    add_promotion_to_uncheck(x[0])
                    await bot.send_message(writer, CHANNEL_WAS_DEL_FROM_CHANNEL(id, LINK_TO_INTRODUCTION_AND_RULES),
                                           parse_mode='Markdown')
            set_last_check()

        await check_user_in_ch()

    elif last_check != None and count_of_channels >= 1:

        now_time = datetime.datetime.now()
        delta = last_check - now_time
        if delta.seconds >= 3600:
            await check_user_in_ch()


# ==============

@dp.message_handler(commands=['start'])
async def start_commands_handle(m: types.Message):
    state = dp.current_state(user=m.from_user.id)
    await state.reset_state()

    if is_user_in_db_tt(m.from_user.id) < 1:
        add_user_to_db_tt(m.from_user.id)
        await m.reply(START, reply=False, parse_mode='HTML', reply_markup=main_menu)
    else:
        await m.reply(UPDATE, reply=False, parse_mode='HTML', reply_markup=main_menu)


@dp.message_handler(lambda m: m.from_user.id in admins, commands=['admin'])
async def admin_command_handle(m: types.Message):
    await m.reply(SELECT_ADMIN_MENU_BUTTON, reply=False, reply_markup=admin_menu)


@dp.message_handler(lambda m: m.from_user.id not in admins, commands=['admin'])
async def handle_not_admin(m: types.Message):
    await m.reply(YOU_WAS_HACK_ME, reply=False)


@dp.message_handler(lambda m: m.text == '👤 Профиль' and user_banned(m.from_user.id) is False)
async def profile_button_handle(m: types.Message):
    await m.reply(PROFILE(m), reply=False, parse_mode='Markdown')


@dp.message_handler(lambda m: m.text == 'Заказать')
async def add_tt_video_handle(m: types.Message):
    state = dp.current_state(user=m.from_user.id)
    await state.set_state('GET_TT_VIDEO')
    await m.reply(GIVE_TT_VIDEO_LINK, reply=False, parse_mode='HTML', reply_markup=cancel_menu)


@dp.message_handler(content_types=['text', 'video'], state='GET_TT_VIDEO')
async def tt_video_handle(m: types.Message):
    try:
        if m.content_type == 'text':
            link = m.text

            # TODO доделать парсер
            if check_tt_link(link):
                pass

            # TODO сохранять видос/линк на него в БД
            number = save_tt_video(client=m.from_user.id, video_link=link)

            cancel_promotion = InlineKeyboardMarkup()
            # TODO добавить эту штуку для удаления видоса в случае нажатия кнопки отмена
            cancel_promotion.add(
                InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_' + str(number)))

            await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)
            await m.reply(SEND_CLIP_COUNT(m.from_user.id, link), reply=False, parse_mode='HTML',
                          reply_markup=cancel_promotion)

            state = dp.current_state(user=m.from_user.id)

            # TODO поменять статус и начать пиар видео
            await state.set_state('SEND_CLIP_COUNT')
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
def check_tt_link(link):
    link_parsed = url_parser.urlparse(link)
    print(link_parsed)
    return link


@dp.message_handler(lambda m: m.text == 'Заработать')
async def sent_instruction_for_subscribe(m: types.Message):
    user_id = m.from_user.id
    # все видосы для продвижения
    video_list = videos_for_work(user_id)
    skipped_videos = get_skipped_videos(user_id)
    # TODO проверить пропущенные видосы и удалять их из списка

    if video_list != 0:
        # выбираем случайный видос
        tt_video_link = random.choice(list(video_list))

        tt_menu = InlineKeyboardMarkup()
        tt_menu.add(InlineKeyboardButton(text='Перейти к TT видео с треком', url=tt_video_link))
        # video_list[tt_video_link] передаем id из БД
        # TODO потом сделать метод проверки видоса через TT API
        tt_menu.add(InlineKeyboardButton(text='Проверить', callback_data='check_' + str(
            video_list[tt_video_link])))
        tt_menu.add(InlineKeyboardButton(text='Пропустить', callback_data='skip_' + str(
            video_list[tt_video_link])))

        await m.reply(RECORD_THIS_TT_VIDEO, reply_markup=tt_menu, reply=False)

        # TODO это в случае ошибки какая-то херня с возвратом денег клиенту
        # writer = edit_promo_status(video_list[video_to_promo], 0)
        # await bot.send_message(writer, CHANNEL_WAS_DEL_FROM_CHANNEL(id, LINK_TO_INTRODUCTION_AND_RULES))

    else:
        await m.reply(NO_TT_VIDEO_TO_PROMO, reply=False)


# TODO старое
@dp.message_handler(lambda m: m.text == '➕ Получить подписчиков' and user_banned(m.from_user.id) == False)
async def add_channel_handle(m: types.Message):
    if user_balance(m.from_user.id) >= LITTLE_SUBCOIN_TO_GET_SUBS:
        state = dp.current_state(user=m.from_user.id)
        await state.set_state('GET_CHANNEL_TO_UP')
        await m.reply(GIVE_CHANNEL_LINK, reply=False, parse_mode='HTML', reply_markup=cancel_menu)
    else:
        await m.reply(LITTLE_SUBCOIN_1, reply=False)


# TODO старое (чекает подписчиков в канале)
@dp.message_handler(state='GET_CHANNEL_TO_UP')
async def channel_to_up_handle(m: types.Message):
    try:

        if m.content_type == 'text':
            my_id = await bot.get_me()
            get_channel = await bot.get_chat(m.text)

            if get_channel.type == 'channel':
                status_bot_in_channel = await bot.get_chat_member(chat_id=m.text, user_id=my_id.id)
                if check_channel_in_db(get_channel.id) == 1:
                    if status_bot_in_channel.status == 'administrator':
                        number = save_channel(channel_id=get_channel.id, writer=m.from_user.id)
                        cancel_promotion = InlineKeyboardMarkup()
                        cancel_promotion.add(
                            InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_' + str(number)))
                        await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)
                        await m.reply(SEND_SUB_COUNT_1(m), reply=False, parse_mode='Markdown',
                                      reply_markup=cancel_promotion)
                        state = dp.current_state(user=m.from_user.id)

                        await state.set_state('GET_SUB_COUNT')
                    else:
                        await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)
                        await m.reply(BOT_NOT_IN_CHANNEL, parse_mode='Markdown', reply_markup=cancel_menu)
                elif check_channel_in_db(get_channel.id) == 0:
                    await m.reply(CHANNEL_ON_PROMOTION_2, reply=False, reply_markup=cancel_menu)
            else:
                await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)
                await m.reply(THIS_IS_NOT_CHANNEL, parse_mode='Markdown', reply_markup=cancel_menu)
        else:

            await m.reply(THIS_IS_NOT_TEXT, parse_mode='Markdown', reply_markup=cancel_menu)

    except Exception as e:
        await m.reply(e, reply_markup=cancel_menu)


# TODO доделать покупку клипов
@dp.message_handler(state='SEND_CLIP_COUNT')
async def handle_send_clip_count(m: types.Message):
    if (m.content_type == 'text') and (m.text.isdigit() is True) and (
            int(m.text) >= 1) and user_balance_tt(m.from_user.id) >= int(m.text) * CASH_MIN:

        video_to_promo_count = int(m.text)
        video_id = update_tt_video_goal(video_to_promo_count)

        confirmation_menu = InlineKeyboardMarkup()
        confirmation_menu.add(
            InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_' + str(video_id)),
            InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm_' + str(video_id)))

        state = dp.current_state(user=m.from_user.id)
        await state.set_state('CONFIRMATION')
        await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)

        # TODO выводить ссылку на видос
        await m.reply(
            CONFIRM_ADDING_CHANNEL(video_id, video_to_promo_count, video_to_promo_count * CASH_MIN),
            reply=False,
            reply_markup=confirmation_menu)
    else:
        video_stat = get_video_stat(m.from_user.id)

        video_id = video_stat[0]
        video_tt_link = video_stat[1][0][0]

        cancel_pay_menu = InlineKeyboardMarkup()
        cancel_pay_menu.add(
            InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_' + str(video_id)))

        await m.reply(LITTLE_SUBCOIN_2, reply=False, reply_markup=cancel_pay_menu)


@dp.message_handler(state='GET_SUB_COUNT')
async def handle_get_sub_count(m: types.Message):
    if (m.content_type == 'text') and (m.text.isdigit() == True) and (
            int(m.text) >= LITTLE_SUBCOIN_TO_GET_SUBS) and user_balance(m.from_user.id) >= int(m.text):
        save_channel(subs_count=int(m.text), writer=m.from_user.id)
        channel_stat = get_channel_stat(m.from_user.id)
        username = await bot.get_chat(channel_stat[0][0][1])
        username = username.username
        confirmation_menu = InlineKeyboardMarkup()
        confirmation_menu.add(
            InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_' + str(channel_stat[-1])),
            InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm_' + str(channel_stat[-1])))
        state = dp.current_state(user=m.from_user.id)
        await state.set_state('CONFIRMATION')
        await bot.delete_message(message_id=m.message_id - 1, chat_id=m.from_user.id)
        await m.reply(CONFIRM_ADDING_CHANNEL(username, channel_stat[0][0][0], channel_stat[0][0][0]), reply=False,
                      reply_markup=confirmation_menu)
    else:
        channel_stat = get_channel_stat(m.from_user.id)
        username = await bot.get_chat(channel_stat[0][0][1])
        username = username.username
        cancel_wnum_menu = InlineKeyboardMarkup()
        cancel_wnum_menu.add(
            InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_' + str(channel_stat[-1])))
        await m.reply(LITTLE_SUBCOIN_2, reply=False, reply_markup=cancel_wnum_menu)


@dp.message_handler(lambda m: m.text == '✔️ Подписаться на канал' and user_banned(m.from_user.id) == False)
async def sent_instruction_for_subscribe(m: types.Message):
    black_list = []
    while True:
        channels_list = channel_for_subscribe(m.from_user.id)
        if channels_list != 0 and len(channels_list) > len(black_list):
            channel_to_subscribe = random.choice(list(channels_list))
            if channel_to_subscribe not in black_list:
                my_id = await bot.get_me()
                try:
                    bot_status = await bot.get_chat_member(chat_id=channel_to_subscribe, user_id=my_id.id)
                    bot_status = bot_status.status
                except (Unauthorized, BotBlocked):
                    bot_status = 'left'

                if bot_status == "administrator":
                    status_of_user = await bot.get_chat_member(chat_id=channel_to_subscribe, user_id=m.from_user.id)
                    if status_of_user.status == 'left':
                        username = await bot.get_chat(chat_id=channel_to_subscribe)
                        subscribe_menu = InlineKeyboardMarkup()
                        subscribe_menu.add(InlineKeyboardButton(text='Перейти к каналу',
                                                                url='tg://resolve?domain=' + username.username))
                        subscribe_menu.add(InlineKeyboardButton(text='Проверить подписку', callback_data='sub_' + str(
                            channels_list[channel_to_subscribe])))
                        await m.reply(SUBSCRIBE_ON_THIS_CHANNEL, reply_markup=subscribe_menu, reply=False)
                        break
                    else:
                        black_list.append(channel_to_subscribe)
                else:
                    writer = edit_promotion_status(channels_list[channel_to_subscribe], 0)
                    id = channel_to_subscribe
                    await bot.send_message(writer, CHANNEL_WAS_DEL_FROM_CHANNEL(id, LINK_TO_INTRODUCTION_AND_RULES))
        else:
            await m.reply(NO_HAVE_CHANNELS_FOR_SUBSCRIBE, reply=False)
            break


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


@dp.message_handler(lambda m: m.text == '👣 Партнёрская программа' and user_banned(m.from_user.id) == False)
async def referal_button_handle(m: types.Message):
    get_bot = await bot.get_me()
    await m.reply(PARTNER_PROGRAM(get_bot.username, m.from_user.id, referals(m.from_user.id)), reply=False,
                  parse_mode='HTML')


@dp.message_handler(lambda m: m.from_user.id in admins, content_types=['text'], state='GET_USER_FOR_CHB')
async def handle_user_for_chb(m: types.Message):
    list = m.text.split(' ')
    if len(list) == 2:
        id = list[0]
        value = list[1]
        if id.isdigit() and value.lstrip('-').isdigit():
            result = change_balance(id, value)
            await m.reply(result, reply=False)
        else:
            await m.reply(NOT_INTEGER, reply=False)
    else:
        await m.reply(LITTLE_VALUE, reply=False)
    state = dp.current_state(user=m.from_user.id)
    await state.reset_state()


@dp.message_handler(lambda m: m.from_user.id in admins, content_types=['text'], state='GET_USER_FOR_UBAN')
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
    number = c.data.replace('cancel_', '')

    status = delete_tt_video_from_db(number)

    if status == 0:
        await c.message.edit_text(TT_VIDEO_ON_PROMOTION)
        state = dp.current_state(user=c.from_user.id)
        await state.reset_state()
    else:
        await c.message.edit_text(CANCEL_TEXT)
        state = dp.current_state(user=c.from_user.id)
        await state.reset_state()


@dp.callback_query_handler(lambda c: 'confirm_' in c.data, state='CONFIRMATION')
async def confirm_button_handler(c: types.callback_query):
    number = c.data.replace('confirm_', '')
    luck = confirm_order(number)
    if luck == 1:
        await c.message.edit_text(CHANNEL_SUCCESSFULLY_ADED)
        state = dp.current_state(user=c.from_user.id)
        await state.reset_state()
    else:
        await c.message.edit_text(luck)
        state = dp.current_state(user=c.from_user.id)
        await state.reset_state()


@dp.callback_query_handler(lambda c: 'sub_' in c.data)
async def check_user_in_channel(c: types.CallbackQuery):
    number = c.data.replace('sub_', '')
    info = promotion_info(number)
    if check_user_to_do_this(number, info[1]) == False:
        if info[0] == 1:
            my_id = await bot.get_me()
            try:
                bot_status = await bot.get_chat_member(chat_id=info[1], user_id=my_id.id)
                bot_status = bot_status.status
            except (Unauthorized, BotBlocked):
                bot_status = 'left'

            if bot_status == "administrator":
                status_of_user = await bot.get_chat_member(chat_id=info[1], user_id=c.from_user.id)
                if status_of_user.status != 'left':
                    add_to_subs = add_user_to_subscribers(number, c.from_user.id)
                    username = await bot.get_chat(chat_id=add_to_subs[1])
                    if add_to_subs[0] == 1:

                        await c.message.edit_text(SUBSCRIBE_IS_SUCCESSFULLY(username.username))
                    else:
                        await c.message.edit_text(YOU_ARE_LATE_FOR_SUBS(username.username))
                else:
                    await c.answer(text=YOU_DONT_COMPLETE_SUBS, show_alert=True)
            else:
                writer = edit_promotion_status(number, 0)
                add_promotion_to_uncheck(number)
                await bot.send_message(writer,
                                       CHANNEL_WAS_DEL_FROM_CHANNEL(add_to_subs[1], LINK_TO_INTRODUCTION_AND_RULES))
        else:
            await c.message.edit_text(YOU_ARE_LATE_FOR_SUBS(username.username))
    else:
        await c.message.edit_text(YOU_DID_THIS)


@dp.callback_query_handler(lambda c: 'skip_' in c.data)
async def skip_video(c: types.CallbackQuery):
    video_id = c.data.replace('skip_', '')
    user_id = c.from_user.id

    add_video_to_skipped(user_id, video_id)

    await bot.send_message(user_id, TT_VIDEO_SKIPPED)

    # info = promotion_info(number)
    # if check_user_to_do_this(number, info[1]) == False:
    #     if info[0] == 1:
    #         my_id = await bot.get_me()
    #         try:
    #             bot_status = await bot.get_chat_member(chat_id=info[1], user_id=my_id.id)
    #             bot_status = bot_status.status
    #         except (Unauthorized, BotBlocked):
    #             bot_status = 'left'
    #
    #         if bot_status == "administrator":
    #             status_of_user = await bot.get_chat_member(chat_id=info[1], user_id=c.from_user.id)
    #             if status_of_user.status != 'left':
    #                 add_to_subs = add_user_to_subscribers(number, c.from_user.id)
    #                 username = await bot.get_chat(chat_id=add_to_subs[1])
    #                 if add_to_subs[0] == 1:
    #
    #                     await c.message.edit_text(SUBSCRIBE_IS_SUCCESSFULLY(username.username))
    #                 else:
    #                     await c.message.edit_text(YOU_ARE_LATE_FOR_SUBS(username.username))
    #             else:
    #                 await c.answer(text=YOU_DONT_COMPLETE_SUBS, show_alert=True)
    #         else:
    #             writer = edit_promotion_status(number, 0)
    #             add_promotion_to_uncheck(number)
    #             await bot.send_message(writer,
    #                                    CHANNEL_WAS_DEL_FROM_CHANNEL(add_to_subs[1], LINK_TO_INTRODUCTION_AND_RULES))
    #     else:
    #         await c.message.edit_text(YOU_ARE_LATE_FOR_SUBS(username.username))
    # else:
    #     await c.message.edit_text(YOU_DID_THIS)


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
