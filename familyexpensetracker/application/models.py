from calendar import c
from enum import unique
from flask_login import UserMixin
from datetime import datetime
from .database import db


class User(db.Model, UserMixin):
    __table_name__='user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) # primary keys are required by db
    name=db.Column(db.String(10),nullable=False,unique=True)
    password = db.Column(db.String(20), nullable=False)
    members=db.relationship("Member",cascade='all',backref="parent")


class Member(db.Model):
    __table_name__='member'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # primary keys are required by db
    name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    total_expense=db.Column(db.Integer,nullable=False)
    expenses=db.relationship("Expense",cascade='all',backref="parent")
    limit=db.Column(db.Integer,nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Expense(db.Model):
    __table_name__='expense'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) # primary keys are required by db
    category = db.Column(db.String, nullable=False)
    amount= db.Column(db.Integer,nullable=False)
    created_date=db.Column(db.DateTime,nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)