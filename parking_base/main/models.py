from datetime import datetime
from typing import Any, Dict

from .app import db
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship


class Parking(db.Model):
    __tablename__ = "parking"

    id = Column(Integer, primary_key=True)
    address = Column(String(100), nullable=False)
    opened = Column(Boolean, default=True)
    count_places = Column(Integer, nullable=False)
    available_places = Column(Integer, nullable=True)

    def __repr__(self):
        return f"Parking id={self.id} at {self.address} opened={self.opened}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Client(db.Model):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    surname = Column(String(50), nullable=False)
    credit_card = Column(String(50), default="")
    car_number = Column(String(10), default="")

    def __repr__(self):
        return f"Client {self.name} {self.surname}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ClientParking(db.Model):
    __tablename__ = "client_parking"
    __table_args__ = (
        UniqueConstraint("client_id", "parking_id", name="unique_cl_parking"),
    )

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    parking_id = Column(Integer, ForeignKey("parking.id"), nullable=False)
    time_in = Column(DateTime, default=datetime.utcnow)
    time_out = Column(DateTime, default=datetime.utcnow)

    p = relationship("Parking", cascade="all,delete", backref="client_parking")
    cl = relationship("Client", cascade="all,delete", backref="client_parking")

    def __repr__(self):
        return (
            f"Client with id={self.client_id} has parking №{self.parking_id} "
            f"from {self.time_in} up to {self.time_out}"
        )

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ParkingLog(db.Model):
    __tablename__ = "parking_log"

    id = Column(Integer, primary_key=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    parking_id = Column(Integer, ForeignKey("parking.id"), nullable=False)
    time_in = Column(DateTime, default=datetime.utcnow)
    time_out = Column(DateTime, default=datetime.utcnow)

    p_lg = relationship("Parking", cascade="all,delete", backref="parking_log")
    cl_lg = relationship("Client", cascade="all,delete", backref="parking_log")

    def __repr__(self):
        return (
            f"Client with id={self.client_id} has parking №{self.parking_id} "
            f"from {self.time_in} up to {self.time_out}"
        )

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
