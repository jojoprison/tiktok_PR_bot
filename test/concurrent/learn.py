with asyncio.get_running_loop() as running_loop:
    payment_future = running_loop.submit(pay_user_for_tasks, user_id, 1)
    payment_sum = payment_future.result()
    await bot.send_message(user_id, 'Поздравляю! Вы получили ' + str(payment_sum) + ' RUB.')