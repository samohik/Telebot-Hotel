import datetime
from pathlib import Path

from peewee import *

BASE_DIR = Path(__file__).resolve().parent
db = SqliteDatabase(BASE_DIR / 'people.db')


class BaseModel(Model):
    class Meta:
        database = db


class HotelInfo(BaseModel):
    city = CharField(verbose_name='City', max_length=50)
    address = CharField(verbose_name='Address', max_length=200)
    price = IntegerField(verbose_name='Price', default=0)

    def __str__(self):
        return str(self.city)


class Image(BaseModel):
    image_url = CharField(max_length=255)
    hotel = ForeignKeyField(HotelInfo, related_name='image', backref='hotel', null=True)


class History(BaseModel):
    command = CharField(verbose_name='Command', max_length=100)
    hotel_history = ForeignKeyField(HotelInfo, related_name='history', backref='hotel', null=True)
    created = DateTimeField(default=datetime.datetime.now)
    user = CharField(max_length=50)


def create_tables():
    with db:
        db.create_tables([HotelInfo, Image, History], safe=True)


if __name__ == '__main__':
    create_tables()
