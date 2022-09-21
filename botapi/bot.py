import re
import traceback
from datetime import datetime, date
from typing import List, Any

import telebot
from loguru import logger
from telebot.types import Message

from config import TOKEN
from models.handlers import save_hotel, save_image, save_history, get_history, create_database
from request import api_get


class HotelBot:
    def __init__(self):
        self.min_distance = str()
        self.max_distance = str()
        self.user = int()
        self.max_price: str = str()
        self.min_price: str = str()
        self.command: str = str()
        self.image: bool = False
        self.img_count: int = int()
        self.pagesize: str = str()
        self.city_id: List = list()
        self.city_name: str = str()
        self.check_in = None
        self.check_out = None
        self.bot = telebot.TeleBot(token=TOKEN)

        @self.bot.message_handler(commands=['start'])
        def buttons(message):
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
            help_b = telebot.types.KeyboardButton('/help')
            low_price = telebot.types.KeyboardButton('/lowprice')
            high_price = telebot.types.KeyboardButton('/highprice')
            best_deal = telebot.types.KeyboardButton('/bestdeal')
            history = telebot.types.KeyboardButton('/history')

            create_database()
            self.user = message.from_user.id
            markup.add(help_b, low_price, high_price, best_deal, history)
            self.bot.send_message(message.chat.id, 'Chose option', reply_markup=markup)

        @self.bot.message_handler(commands=['help'])
        def low_price_command(message: Message) -> None:
            """
            Get help.
            :param message: Message
            :return: None
            """
            help_text = """
            /start - запуск бота, выполняется автоматически при подключении к боту.
            /help - список команд и их описание
            /lowprice - топ дешевых отелей
            /highprice - топ дорогих отелей
            /bestdeal - лучшие предложения
            """
            # / settings - меню с настройками
            self.bot.reply_to(message, help_text)

        @self.bot.message_handler(commands=['lowprice'])
        def low_price_command(message: Message) -> None:
            """
            Get city name from user.
            :param message: Message
            :return: None
            """
            self.command = 'PRICE'
            self.redirect_reply_to(message, self.process_name, 'Где ищем?')

        @self.bot.message_handler(commands=['highprice'])
        def high_price_command(message: Message) -> None:
            """
            Get city name from user.
            :param message: Message
            :return: None
            """
            self.command = 'PRICE_HIGHEST_FIRST'
            self.redirect_reply_to(message, self.process_name, 'Где ищем?')

        @self.bot.message_handler(commands=['bestdeal'])
        def best_dial_command(message: Message) -> None:
            """
            Get city name from user.
            :param message: Message
            :return: None
            """
            self.command = 'DISTANCE_FROM_LANDMARK'
            self.redirect_reply_to(message, self.ask_min_price, 'Минимальная цена ?')

        @self.bot.message_handler(commands=['history'])
        def best_dial_command(message: Message) -> None:
            """
            Get history.
            :param message: Message
            :return: None
            """
            self.redirect_reply_to(message, self.ask_max_history_list, 'Сколько вызовов ?')

    def ask_max_history_list(self, message: Message) -> None:
        """
        Asks how many lines to display
        :param message: Message
        :return: None
        """
        number = message.text
        pattern = r'^\d$'
        if re.findall(pattern, number):
            history = get_history(user=self.user, number=number)
            number_call: int = 0
            for elem in history:
                number_call += 1
                self.bot.send_message(
                    message.chat.id,
                    f'Команда: {elem.command}\n'
                    f'Город: {elem.hotel_history.city}\n'
                    f'Адрес: {elem.hotel_history.address}\n'
                    f'Цена: {elem.hotel_history.price}\n'
                    f'Дата: {elem.created.strftime("%Y/%m/%d %H:%M:%S")}'
                )
            self.bot.send_message(message.chat.id, f'{number_call} записей найдена')
        else:
            self.redirect_send_method(message, self.ask_max_history_list, 'Сколько вызовов ?')

    def ask_min_price(self, message: Message) -> None:
        """
        Ask user min_price.
        :param message: Messages
        :return: None
        """
        self.min_price = self.handlers(
            message,
            pattern=r'^\d+$',
            successful_func=self.ask_max_price,
            try_func=self.ask_min_price,
            successful_mess='Максимальная цена ?',
            incorrect_mess='Введите минимальное число',
            try_mess='Минимальная цена должна быть больше нуля',
        )
        logger.info(f'Message min_price: {self.min_price}')

    def ask_max_price(self, message: Message) -> None:
        """
        Ask user max_price.
        :param message: Messages
        :return: None
        """
        self.max_price = self.handlers(
            message,
            pattern=r'^\d+$',
            successful_func=self.ask_min_distance,
            try_func=self.ask_max_price,
            min_val=int(self.min_price),
            successful_mess='Какое минимальное расстояние от центра в км?',
            incorrect_mess='Максимальная цена ?',
            try_mess='Максимальная цена должна быть больше минимальной ?',
        )
        logger.info(f'Message max_price: {self.max_price}')

    def ask_min_distance(self, message: Message) -> None:
        """

        :param message: Message
        :return: None
        """
        self.min_distance = self.handlers(
            message,
            pattern=r'^(\d+[.,]?\d+|\d)',
            successful_func=self.ask_max_distance,
            try_func=self.ask_min_distance,
            successful_mess='Какое максимальное расстояние от центра в км?',
            incorrect_mess='В видите число в км',
            try_mess='Минимальное расстояние '
                     'должно быть больше нуля',
        )
        logger.info(f'Message min_distance: {self.min_distance}')

    def ask_max_distance(self, message: Message) -> None:
        """

        :param message: Message
        :return: None
        """
        self.max_distance = self.handlers(
            message,
            pattern=r'^(\d+[.,]?\d+|\d)',
            successful_func=self.process_name,
            try_func=self.ask_max_price,
            min_val=float(self.min_distance),
            successful_mess='Где ищем ?',
            incorrect_mess='В видите число в км',
            try_mess='Максимальное расстояние '
                     'должно быть больше минимального',
        )
        logger.info(f'Message max_distance: {self.max_distance}')

    def process_name(self, message: Message) -> None:
        """
        Check name if correct get city_id else try again.
        :param message: Message
        :return: None
        """
        self.city_name = message.text.lower()
        patterns = r'^[A-zА-я]+[ ]?[A-zА-я]+$'

        if re.findall(patterns, self.city_name):
            logger.info(f'City name: {self.city_name}')

            id_city = api_get.get_id_city(city_name=self.city_name)
            logger.info(f'Check city name {id_city}')
            if id_city:
                self.city_id = id_city
                self.redirect_send_method(message, self.max_lines, 'Сколько стр(макс 25)?')

            else:
                self.redirect_send_method(message, self.process_name, 'Dont exists try again')

        else:
            logger.info(f'Patterns dont match')
            self.redirect_send_method(message, self.process_name, 'Try again')

    def max_lines(self, message: Message) -> None:
        """
        Ask user max page.
        :param message: Messages
        :return: None
        """
        self.pagesize = message.text
        logger.info(f'Message max: {self.pagesize}')

        self.redirect_send_method(message, self.check_image, 'Выводить фотографии?')

    def check_image(self, message: Message) -> None:
        """
        Asks the user for photos.
        :param message: Message
        :return: None
        """
        pattern_yes = r'^[Yy]es|[Дд]а$'
        pattern_no = r'^[Nn]o|[Нн]ет$'

        if re.findall(pattern_yes, message.text):
            self.image = True
            logger.info(f'Image: "{self.image}"')
            self.redirect_send_method(message, self.image_count, 'Количество необходимых фотографий (макс. 5)?')

        elif re.findall(pattern_no, message.text):
            self.image = False
            logger.info(f'Image: "{self.image}"')
            self.redirect_send_method(message, self.check_In, 'Дата въезда (пример: "2020-01-08")?')

        else:
            logger.error(f'Incorrect input')
            self.redirect_send_method(message, self.check_image, 'Yes or no ?')

    def image_count(self, message: Message) -> None:
        """
        Asks the user how many photos they need.
        :param message: Message
        :return: None
        """
        if 0 < int(message.text) <= 5:
            self.img_count = int(message.text)
            self.redirect_send_method(message, self.check_In, 'Дата въезда (пример: "2020-01-08")?')
        else:
            self.redirect_send_method(message, self.image_count, 'Количество необходимых фотографий ?')

    def check_In(self, message: Message) -> None:
        """
        Asks the user the date of entry.
        :param message: Message
        :return: None
        """
        self.check_in = self.check_patterns(message, self.check_In,
                                            try_message='Некорректные данные: {error}\nДата въезда (пример: '
                                                        '"2020-01-08")?')
        if self.check_in:
            logger.info(f'Message check in: {self.check_in}')
            self.redirect_send_method(message, self.check_Out, 'Дата выезда (пример: "2020-01-15")?')

    def check_Out(self, message: Message) -> None:
        """
        Ask user when out.
        :param message: Message
        :return: None
        """
        self.check_out = self.check_patterns(message, self.check_Out,
                                             try_message='Некорректные данные: {error}\nДата выезда (пример: '
                                                         '"2020-01-15")?')
        if self.check_out:
            subtract = self.check_out - self.check_in
            if subtract.days > 0:
                logger.info(f'Message check out : {self.check_out}')
                self.print_func(message)
            else:
                self.redirect_send_method(message, self.check_Out,
                                          'Try again\nДата выезда (пример: "2020-01-15")?')

    def print_func(self, message: Message) -> None:
        """
        Send message to user with info and image.
        :param message: Message
        :return: None
        """
        try:
            if self.command == 'DISTANCE_FROM_LANDMARK':
                result = self.best_deal_sort()
            else:
                result = self.get_hotel_info(self.pagesize)
            number_call: int = 0
            for elem in result:
                number_call += 1

                hotel = save_hotel(elem=elem)

                if self.image:
                    image = api_get.image(hotel_id=elem["hotel_id"],
                                          count=self.img_count)
                    for val in image.values():
                        self.bot.send_photo(
                            chat_id=message.chat.id,
                            photo=f'{(val["url"]).format(size=val["size"])}')

                        save_image(hotel, val)

                self.bot.send_message(
                    message.chat.id,
                    f'Name: {elem["name"]}\n'
                    f'Link: hotels.com/ho{elem["hotel_id"]}\n'
                    f'Address: {elem["address"]}\n'
                    f'Distance from center: {elem["landmarks"]}\n'
                    f'Price: ${elem["price"]}\n'
                    f'Price per week: ${elem["price_weeks"]}\n'
                )

                save_history(user=self.user, hotel=hotel, command=self.command)

            self.bot.send_message(message.chat.id, f'Всего нашло отелей: {number_call}')

        except api_get.BadRequest as e:
            logger.error(f"{e}\n{traceback.format_exc()}")
            self.bot.send_message(message.chat.id, f'Нет связи')

    def best_deal_sort(self) -> list[dict[str, Any]]:
        """
        Checks the distance from the center and generates a list.
        :return: List
        """
        res = self.get_hotel_info(pageSize='25')
        sorted_list = list()
        count = 0
        for hotel in res:
            if count == int(self.pagesize):
                break
            land = hotel['landmarks']
            distance = re.findall(r'^(\d+[.,]?\d+|\d)', land)
            distance = distance[0].replace(',', '.')
            if float(self.max_distance) >= float(distance) >= float(self.min_distance):
                sorted_list.append(hotel)
                count += 1
        return sorted_list

    def get_hotel_info(self, pageSize) -> list[dict[str, Any]]:
        """
        There is a call to api hotels.
        :return: list[dict[str, Any]
        """
        list_val = api_get.hotel_info(
            price_min=self.min_price,
            price_max=self.max_price,
            sort_order=self.command,
            page_size=pageSize,
            city_id=self.city_id[0],
            check_in=self.check_in,
            check_out=self.check_out)

        return list_val

    def handlers(self, message, pattern, successful_func, try_func, successful_mess,
                 incorrect_mess, try_mess, min_val: Any = 0) -> Any:
        """
        Processes the max and min responses from the user.
        :param message: Message
        :param pattern: response pattern
        :param successful_func: next function
        :param try_func: ask again function
        :param min_val: comparison value
        :param successful_mess: message on successful response
        :param incorrect_mess: message for incorrect answer
        :param try_mess: message to repeat reply
        :return: None
        """
        valid = re.findall(pattern, message.text)
        if valid:
            distance = valid[0].replace(',', '.')
            if float(distance) > min_val:
                val = distance
                self.redirect_send_method(message, successful_func, successful_mess)
                return val
            else:
                self.redirect_send_method(message, try_func, try_mess)
        else:
            self.redirect_send_method(message, try_func, incorrect_mess)

    def redirect_reply_to(self, message: Message, func, question: str) -> None:
        """
        Produces a redirect with a message to the user.
        :param message: Message
        :param func: which function to redirect to
        :param question: what message to send to the user
        :return: None
        """
        self.bot.reply_to(message, question)
        self.bot.register_next_step_handler(message, func)
        logger.info(f'Redirect to "{func.__name__}"')

    def redirect_send_method(self, message: Message, func, question: str, error: str = str()) -> None:
        """
        Produces a redirect with a message to the user.
        :param error: Error if occur
        :param message: Message
        :param func: which function to redirect to
        :param question: what message to send to the user
        :return: None
        """
        self.bot.send_message(message.chat.id, question.format(error=error))
        self.bot.register_next_step_handler(message, func)
        logger.info(f'Redirect to "{func.__name__}"')

    def check_patterns(self, message: Message, func, try_message: str) -> date:
        """
        Checks for a pattern if it doesn't pass redirects.
        :param message: Message
        :param func: redirect to this function
        :param try_message: messages for the user
        :return: str
        """
        pattern = r'^2[\d]{3}-[01]\d-[0123]\d$'
        try:
            if re.findall(pattern, message.text):
                datetime_obj = datetime.strptime(message.text, '%Y-%m-%d')
                return datetime_obj.date()
            else:
                self.redirect_send_method(message, func, try_message)

        except ValueError as e:
            logger.error(f'{e}')
            self.redirect_send_method(message, func, try_message, error=str(e))

    def run(self):
        self.bot.infinity_polling()


if __name__ == '__main__':
    bot = HotelBot()
    bot.run()
