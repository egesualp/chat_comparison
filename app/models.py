from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import JSON

Base = declarative_base()

class RunRecord(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    system_prompt = Column(Text)
    user_prompt = Column(Text)
    models = Column(Text)
    temperature = Column(Float)
    top_p = Column(Float)
    max_tokens = Column(Integer)
    frequency_penalty = Column(Float)
    presence_penalty = Column(Float)
    results = Column(JSON)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    cost = Column(Float)
