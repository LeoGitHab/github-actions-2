from datetime import datetime, timedelta
from typing import List

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking_base.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    from .models import Client, ClientParking, Parking, ParkingLog

    @app.before_first_request
    def before_request_func():
        db.create_all()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    @app.route("/test_route")
    def math_route():
        """Тестовый роут для расчета степени"""
        number = int(request.args.get("number", 0))
        result = number**2
        return jsonify(result)

    @app.route("/clients", methods=["POST"])
    def create_client_handler():
        """Создание нового клиента"""
        name = request.form.get("name", type=str)
        surname = request.form.get("surname", type=str)
        card = request.form.get("credit_card", type=str)
        car_num = request.form.get("car_number", type=str)

        new_user = Client(
            name=name, surname=surname, credit_card=card, car_number=car_num
        )

        db.session.add(new_user)
        db.session.commit()

        return "", 201

    @app.route("/clients", methods=["GET"])
    def get_all_clients():
        """Получение всех клиентов"""
        clients: List[Client] = db.session.query(Client).all()
        clients_list = [cl.to_json() for cl in clients]
        return jsonify(clients_list), 200

    @app.route("/clients/<int:client_id>", methods=["GET"])
    def get_client_by_id(client_id: int):
        """Получение клиента по id"""
        id_exist = bool(Client.query.filter_by(id=client_id).first())
        if id_exist:
            client: Client = db.session.query(Client).get(client_id)
            return jsonify(client.to_json()), 200

        return f"Client with id={client_id} is not exist.", 404

    @app.route("/clients", methods=["DELETE"])
    def delete_client_by_id():
        """Удаление клиента по id"""
        client_id = request.form.get("client_id", type=int)
        id_exist = bool(Client.query.filter_by(id=client_id).first())
        if id_exist:
            db.session.query(Client).filter(Client.id == client_id).delete()
            db.session.commit()
            return f"Client with id={client_id} successfully deleted.", 200

        return f"Client with id={client_id} is not exist.", 404

    @app.route("/parking", methods=["GET"])
    def get_all_parking_places():
        """Получение информации обо всех парковках"""
        parking: List[Parking] = db.session.query(Parking).all()
        parking_list = [c.to_json() for c in parking]
        return jsonify(parking_list), 200

    @app.route("/parking", methods=["POST"])
    def create_new_parking():
        """Создание новой парковки"""
        address = request.form.get("address", type=str)
        count_places = request.form.get("count_places", type=int)

        new_parking_place = Parking(
            address=address,
            count_places=count_places,
            available_places=count_places,
        )

        db.session.add(new_parking_place)
        db.session.commit()
        return "", 201

    @app.route("/client_parking", methods=["GET"])
    def get_all_parked_clients():
        """Получение всех припаркованных клиентов"""
        clients: List[ClientParking] = db.session.query(ClientParking).all()
        clients_list = [cl.to_json() for cl in clients]
        return jsonify(clients_list), 200

    @app.route("/client_parking", methods=["POST"])
    def moving_the_car_to_the_parking_place():
        """Заезд автомобиля на парковку"""
        client_id = request.form.get("client_id", type=int)
        parking_id = request.form.get("parking_id", type=int)

        credit_card_check = (
            db.session.query(Client.credit_card)
            .where(Client.id == client_id)
            .one_or_none()
        )

        if credit_card_check is None or credit_card_check[0] == "":
            return f"Client with id={client_id} does not have any card.", 400

        parking_place_open = (
            db.session.query(Parking.opened)
            .where(Parking.id == parking_id)
            .one_or_none()
        )

        available_places = (
            db.session.query(Parking.available_places)
            .where(Parking.id == parking_id)
            .one()[0]
        )

        if (
            parking_place_open is None
            or parking_place_open[0] is False
            or (available_places - 1) < 0
        ):
            return f"Parking with id={parking_id} is not available.", 404

        db.session.query(Parking).filter(Parking.id == parking_id).update(
            {Parking.available_places: (available_places - 1)}
        )

        time_in = datetime.utcnow()
        time_out = datetime.utcnow() + timedelta(days=0, hours=5)

        new_happy_car = ClientParking(
            client_id=client_id,
            parking_id=parking_id,
            time_in=time_in,
            time_out=time_out,
        )
        db.session.add(new_happy_car)
        db.session.commit()

        new_happy_car_log = ParkingLog(
            client_id=client_id,
            parking_id=parking_id,
            time_in=time_in,
            time_out=time_out,
        )
        db.session.add(new_happy_car_log)
        db.session.commit()

        return "", 201

    @app.route("/client_parking", methods=["DELETE"])
    def delete_client_from_parking():
        cl_id = request.form.get("client_id", type=int)
        park_id = request.form.get("parking_id", type=int)

        record_exists = bool(
            ClientParking.query.filter(
                and_(
                    ClientParking.client_id == cl_id,
                    ClientParking.parking_id == park_id,
                )
            ).first()
        )

        if not record_exists:
            return "Combo client_id, and parking_id is not exist.", 404

        db.session.query(ParkingLog).filter(
            and_(
                ParkingLog.client_id == cl_id,
                ParkingLog.parking_id == park_id,
            )
        ).update({ParkingLog.time_out: datetime.utcnow()})

        db.session.query(ClientParking).filter(
            and_(
                ClientParking.client_id == cl_id,
                ClientParking.parking_id == park_id,
            )
        ).delete()

        db.session.query(Parking).filter(Parking.id == park_id).update(
            {Parking.available_places: (Parking.available_places + 1)}
        )

        db.session.commit()

        return "", 200

    @app.route("/parking_log", methods=["GET"])
    def get_history_about_all_parked_clients():
        """Получение истории всех припаркованных клиентов"""
        clients: List[ParkingLog] = db.session.query(ParkingLog).all()
        clients_list = [cl.to_json() for cl in clients]
        return jsonify(clients_list), 200

    return app
