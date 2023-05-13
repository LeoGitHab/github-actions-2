import pytest

from datetime import datetime, timedelta
from .main.app import create_app, db as _db
from .main.models import Client, Parking, ClientParking, ParkingLog


@pytest.fixture()
def app():
    _app = create_app()
    _app.config['TESTING'] = True
    _app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

    with _app.app_context():
        _db.create_all()
        parking = Parking(id=1,
                          address='Nowhere, 0',
                          opened=True,
                          count_places=2,
                          count_available_places=2)
        client_1 = Client(id=1,
                          name='name',
                          surname='surname',
                          credit_card='00000',
                          car_number='0000XXX00')
        client_2 = Client(id=2,
                          name='another_name',
                          surname='another_surname',
                          credit_card='22222',
                          car_number='2222XXX22')
        client_parking = ClientParking(id=1,
                                       client_id=1,
                                       parking_id=1,
                                       time_in=datetime.utcnow(),
                                       time_out=datetime.utcnow())
        parking_log = ParkingLog(id=1,
                                 client_id=1,
                                 parking_id=1,
                                 time_in=datetime.utcnow(),
                                 time_out=datetime.utcnow() + timedelta(days=1))
        _db.session.add(parking)
        _db.session.add(client_1)
        _db.session.add(client_2)
        _db.session.add(client_parking)
        _db.session.add(parking_log)
        _db.session.commit()

        yield _app
        _db.session.close()
        _db.drop_all()


@pytest.fixture
def client(app):
    client = app.test_client()
    yield client


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
