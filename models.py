import os
import datetime

from extensions import db


class Payment(db.Model):
    __tablename__ = 'payment'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10,2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'{self.id}:{self.amount}:{self.currency} - {self.description}'
