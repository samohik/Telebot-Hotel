from typing import Any, Type

from loguru import logger

from models.orm import Image, History, HotelInfo, create_tables


def create_database():
    """
    Create database.
    :return: None
    """
    create_tables()
    logger.debug(f'Database created')


def get_history(user: int, number: str) -> list:
    """
    Returns a sorted list.
    :param user: id user
    :param number: Number of calls
    :return: List
    """
    return History.select().where(History.user == str(user)).order_by(History.created.desc()).limit(number)


def save_hotel(elem: dict[str: Any]) -> Type[HotelInfo]:
    """
    Save Hotel info
    :param elem: dict
    :return: instance HotelInfo
    """
    hotel = HotelInfo.create(
        city=elem["name"], address=elem["address"], price=elem["price"],
    )
    logger.debug(f'Instance HotelInfo created')
    return hotel


def save_image(hotel, val: dict[str: Any]):
    """
    Save image
    :param hotel: instance HotelInfo
    :param val: dict
    :return: None
    """
    Image.create(
        image_url=f'{(val["url"]).format(size=val["size"])}',
        hotel=hotel,
    )
    logger.debug(f'Instance Image save')


def save_history(command: str, user, hotel):
    """
    Save History
    :param command: sorting method
    :param user: instance Profile
    :param hotel: instance HotelInfo
    :return: None
    """
    call_method = str()
    if command == 'PRICE':
        call_method = '/lowprice'

    elif command == 'PRICE_HIGHEST_FIRST':
        call_method = '/highprice'

    elif command == 'DISTANCE_FROM_LANDMARK':
        call_method = '/bestdeal'

    History.create(hotel_history=hotel, user=user, command=call_method)
    logger.debug(f'History {hotel} save')
