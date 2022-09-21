import json
import traceback
from typing import Any

import requests
from loguru import logger

from config import KEY

headers = {
    "X-RapidAPI-Key": KEY,
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
}

destinationId = "1506246"


class BadRequest(BaseException):
    pass


def get_response(querystring, url) -> Any:
    """

    :param url:
    :param querystring:
    :return:
    """
    response = requests.request("GET", url, headers=headers, params=querystring, timeout=30)
    if response.status_code == 200:
        data_json = json.loads(response.text)
        return data_json
    raise BadRequest


def image(hotel_id: str = '634418464', count: int = 1) -> dict[int, dict[str, Any]]:
    """
    Find images.
    :param count: how much image return
    :param hotel_id: hotel id
    :return: list
    """
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"

    dict_img = dict()
    querystring = {"id": hotel_id}

    data_json = get_response(querystring, url)

    for num in range(count):
        base_url = data_json['hotelImages'][num]['baseUrl']
        size = data_json['hotelImages'][num]['sizes'][1]['suffix']
        dict_img[num] = {'url': base_url, 'size': size}

    return dict_img


def hotel_info(
        # locale: str = 'en_US',
        locale: str = 'ru_RU',
        price_min: str = str(),
        price_max: str = str(),
        city_id: str = '1490707',
        sort_order: str = "PRICE",
        page_size: str = "10",
        currency: str = "USD",
        check_in: str = "2020-01-08",
        check_out: str = "2020-01-15"
) -> list[dict[str, Any]]:
    list_money = list()

    url = "https://hotels4.p.rapidapi.com/properties/list"
    querystring = {
        "priceMin": price_min,
        "priceMax": price_max,
        "destinationId": city_id,
        "pageNumber": "1",
        "pageSize": page_size,
        "checkIn": check_in,
        "checkOut": check_out,
        "adults1": "1",
        "sortOrder": sort_order,
        "locale": locale,
        "currency": currency
    }
    data_json = get_response(querystring, url)

    try:
        list_result = data_json['data']['body']['searchResults']['results']
        for index, elem in enumerate(list_result):
            try:
                address = elem['address']['streetAddress']
                landmarks = elem['landmarks'][0]['distance']
                name = elem['name']
                price = elem['ratePlan']['price']['exactCurrent']
                price_weeks = round(price * 7, 2)
                hotel_id = elem['id']

                list_money.append({
                    'hotel_id': hotel_id, 'name': name,
                    'address': address,
                    'price': price,
                    'landmarks': landmarks,
                    'price_weeks': price_weeks
                })
            except KeyError:
                continue

    except KeyError as e:
        logger.error(f'hotel_info: {e}\n{traceback.format_exc()}')

    return list_money


def get_id_city(
        city_name="new york",
        # locale="en_US",
        locale="ru_RU",
        currency="USD"
) -> list[Any]:
    city_id_list = list()

    url = "https://hotels4.p.rapidapi.com/locations/v2/search"
    querystring = {"query": city_name, "locale": locale, "currency": currency}

    data_json = get_response(querystring, url)

    type_list = data_json['suggestions']
    try:
        for list_v in type_list:
            if list_v['group'] in ['CITY_GROUP']:
                for x in list_v['entities']:
                    if x['name'].lower() == city_name.lower():
                        city_id_list.append(x['destinationId'])
                        break
    except KeyError as e:
        logger.error(e)

    return city_id_list


if __name__ == '__main__':
    pass
    # print(hotel_info())
