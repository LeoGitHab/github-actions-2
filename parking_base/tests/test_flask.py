import json
import pytest

from main.models import Client, Parking, ClientParking, ParkingLog
from sqlalchemy import func


def test_app_config(app):
    assert not app.config['DEBUG']
    assert app.config['TESTING']
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite://'


def test_math_route(client) -> None:
    resp = client.get("/test_route?number=9")
    data = json.loads(resp.data.decode())
    assert data == 81


def test_user(client) -> None:
    resp = client.get("/clients/1")
    assert resp.status_code == 200
    assert resp.json == {'id': 1, 'name': 'name', 'surname': 'surname',
                         'credit_card': '00000', 'car_number': '0000XXX00'}


def test_create_user(client) -> None:
    user_data = {'name': 'second_name', 'surname': 'second_surname',
                 'credit_card': 'second_credit_card', 'car_number': "second_car_number"}
    resp = client.post("/clients", data=user_data)

    assert resp.status_code == 201


def test_create_parking(client) -> None:
    parking_data = {'address': 'Second_nowhere, 0', 'opened': True,
                    'count_places': 2, 'count_available_places': 2}
    resp = client.post("/parking", data=parking_data)

    assert resp.status_code == 201


@pytest.mark.parametrize('route', ['/test_route?number=9', '/clients', '/clients/1',
                                   '/parking', '/parking_log', '/client_parking'])
def test_route_status(client, route):
    rv = client.get(route)
    assert rv.status_code == 200


@pytest.mark.parking
def test_client_go_to_parking(client, db):
    client_parking_data = {'client_id': 2, 'parking_id': 1}

    counter_before_entering_to_parking = db.session.query(
        Parking.count_available_places).filter(Parking.id == client_parking_data['parking_id']).one()[0]
    resp = client.post("/client_parking", data=client_parking_data)
    counter_after_entering_to_parking = db.session.query(
        Parking.count_available_places).filter(Parking.id == client_parking_data['parking_id']).one()[0]

    assert resp.status_code == 201
    assert counter_before_entering_to_parking == 2
    assert counter_after_entering_to_parking == 1


@pytest.mark.parking
def test_client_go_out_of_parking(client, db):
    client_parking_data = {'client_id': 1, 'parking_id': 1}

    counter_before_go_out_of_parking = db.session.query(
        Parking.count_available_places).filter(Parking.id == client_parking_data['parking_id']).one()[0]

    records_before_go_out_of_parking = db.session.query(func.count(ClientParking.id)).scalar()

    resp = client.delete("/client_parking", data=client_parking_data)

    counter_after_go_out_of_parking = db.session.query(
        Parking.count_available_places).filter(Parking.id == client_parking_data['parking_id']).one()[0]

    records_after_go_out_of_parking = db.session.query(func.count(ClientParking.id)).scalar()

    assert resp.status_code == 200
    assert counter_before_go_out_of_parking == 2
    assert counter_after_go_out_of_parking == 3
    assert records_before_go_out_of_parking == 1
    assert records_after_go_out_of_parking == 0
