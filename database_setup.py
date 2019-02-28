# Configuration
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required

Base = declarative_base()

class Architect(Base):
    __tablename__ = 'architect'

    id = Column(Integer, primary_key = True)
    office = Column(String(80))
    name = Column(String(80))
    website = Column(String(250))

class Customer(Base):
  # Table
  __tablename__ = 'customer'

  # Mapper
  id = Column(Integer, primary_key = True)
  name = Column(String(80), nullable = False)
  type = Column(String(250), nullable = False)

class Picture(Base):
  # Table
  __tablename__ = 'picture'

  # Mapper
  id = Column(Integer, primary_key = True)
  path = Column(String(250), nullable = False)


class Project(Base):
    __tablename__ = 'project'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    style = Column(String(250), nullable = False)
    type = Column(String(250), nullable = False)
    description = Column(String(), nullable = False)
    contribution = Column(String(250), nullable = False)
    video = Column(String(255))

    # Relationships
    architect_id = Column(Integer, ForeignKey('architect.id'))
    customer_id = Column(Integer, ForeignKey('customer.id'))
    profile_pic_id = Column(Integer, ForeignKey('picture.id'))

    # Table Mapper
    architect = relationship(Architect)
    customer = relationship(Customer)
    picture = relationship(Picture)



class projectPicture(Base):
    __tablename__ = 'project_picture'

    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    picture_id = Column(Integer, ForeignKey('picture.id'), primary_key=True)

    project = relationship(Project)
    picture = relationship(Picture)

class customerPicture(Base):
    __tablename__ = 'customer_picture'

    Customer_id = Column(Integer, ForeignKey('customer.id'), primary_key=True)
    picture_id = Column(Integer, ForeignKey('picture.id'), primary_key=True)

    customer = relationship(Customer)
    picture = relationship(Picture)

class architectPicture(Base):
    __tablename__ = 'architect_picture'

    architect_id = Column(Integer, ForeignKey('architect.id'), primary_key=True)
    picture_id = Column(Integer, ForeignKey('picture.id'), primary_key=True)

    architect = relationship(Architect)
    picture = relationship(Picture)

# Configuration
engine = create_engine('sqlite:///icu.db')
Base.metadata.create_all(engine)
