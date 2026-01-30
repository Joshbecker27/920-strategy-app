from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import json

Base = declarative_base()

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String)
    direction = Column(String)
    score = Column(Integer)
    entry = Column(Float)
    stop = Column(Float)
    target1 = Column(Float)
    target2 = Column(Float)
    ema9 = Column(Float)
    ema20 = Column(Float)
    vwap = Column(Float)
    price = Column(Float)
    time = Column(DateTime)
    reason = Column(String)  # Store as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

class Database:
    def __init__(self):
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./920_alerts.db')
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def save_alert(self, alert_data):
        """Save an alert to database"""
        # Convert reason list to JSON string
        alert_copy = alert_data.copy()
        alert_copy['reason'] = json.dumps(alert_data['reason'])
        
        alert = Alert(**alert_copy)
        self.session.add(alert)
        self.session.commit()
        return alert.id
    
    def get_recent_alerts(self, limit=50):
        """Get recent alerts"""
        alerts = self.session.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()
        return [self._alert_to_dict(a) for a in alerts]
    
    def _alert_to_dict(self, alert):
        return {
            'id': alert.id,
            'ticker': alert.ticker,
            'direction': alert.direction,
            'score': alert.score,
            'entry': alert.entry,
            'stop': alert.stop,
            'target1': alert.target1,
            'target2': alert.target2,
            'ema9': alert.ema9,
            'ema20': alert.ema20,
            'vwap': alert.vwap,
            'price': alert.price,
            'time': alert.time.isoformat() if alert.time else None,
            'reason': json.loads(alert.reason) if alert.reason else [],
            'created_at': alert.created_at.isoformat()
        }