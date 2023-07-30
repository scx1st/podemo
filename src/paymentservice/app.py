import os
import random
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://otel:otel321@localhost/bookdb'
CORS(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)
    payed_at = db.Column(db.DateTime, server_default=db.func.now())
    

@app.route('/api/payments', methods=['POST'])
def create_payment():
    # 实际场景更多会从消息队列中去获取订单信息
    # 这里为了方便，直接从请求中获取
    order_id = request.json.get('order_id')
    # TODO：应该先从 Header 中获取 JWT Token，然后请求用户服务获取用户信息
    token = request.headers.get('Authorization')
    # token = tokenStr.replace('Bearer ', '')
    
    user_id = request.json.get('user_id')
    amount = request.json.get('amount')

    # 模拟支付过程，随机 Sleep 0.5-2 秒
    time.sleep(random.randint(5, 20) / 10)
    
    payment = Payment(
        order_id=order_id, 
        user_id=user_id, 
        amount=amount,
        status=1
    )
    db.session.add(payment)
    db.session.commit()
     
    # TODO：应该发送消息到消息队列，通知订单服务更新订单状态
    # 这里为了方便，直接调用订单服务的 API 来处理
    requests.post('{}/api/orders/{}/status/{}'.format(os.getenv("ORDER_SERVICE_URL"), order_id, 2),
        headers={
            "Authorization": token
        }
    )
    # TODO：记录日志
    return jsonify({'id': payment.id}), 201


@app.route('/api/payments', methods=['GET'])
def get_payments():
    payments = Payment.query.all()
    return jsonify([{'id': p.id, 'order_id': p.order_id, 'user_id': p.user_id, 'amount': p.amount} for p in payments])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083, debug=True)
    