import os
import random
import time
import requests
from flask import Flask, request, jsonify, g, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from tracer import tracer
from opentelemetry.trace import Status, StatusCode
from opentelemetry.semconv.trace import SpanAttributes


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://otel:otel321@localhost/bookdb'
CORS(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

def jwt_middleware():
    def middleware():
        # 从 Header 中获取 JWT Token
        token = request.headers.get('Authorization')
        if not token:
            abort(401, "Token is missing")

        # 请求用户服务获取用户信息
        response = requests.get(os.getenv("USER_SERVICE_URL") + '/api/userinfo', headers={"Authorization": token})
        # 检查响应状态
        if response.status_code != 200:
            abort(401, "Invalid Token")

        user_info = response.json()
        print(user_info)
        g.user_info = user_info

    return middleware

# 注册中间件
app.before_request(jwt_middleware())


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)
    payed_at = db.Column(db.DateTime, server_default=db.func.now())
    

@app.route('/api/payments', methods=['POST'])
def create_payment():
    with tracer.start_as_current_span("POST /api/payments") as span:
        span.set_attribute(SpanAttributes.HTTP_METHOD, "POST")
        span.set_attribute(SpanAttributes.HTTP_URL, "/api/payments")

        # 实际场景更多会从消息队列中去获取订单信息
        # 这里为了方便，直接从请求中获取
        order_id = request.json.get('order_id')
        # 应该先从 Header 中获取 JWT Token，然后请求用户服务获取用户信息
        token = request.headers.get('Authorization')
        # token = tokenStr.replace('Bearer ', '')

        # user_id = request.json.get('user_id')
        # 从 g.user_info 从获取用户信息
        user_id = g.user_info.get('id')

        amount = request.json.get('amount')

        span.set_attribute("order_id", order_id)
        span.set_attribute("user_id", user_id)

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

        # 记录事件
        span.add_event("payment_created", {"order_id": order_id, "user_id": user_id, "amount": amount})

        # TODO：应该发送消息到消息队列，通知订单服务更新订单状态
        # 这里为了方便，直接调用订单服务的 API 来处理
        requests.post('{}/api/orders/{}/status/{}'.format(os.getenv("ORDER_SERVICE_URL"), order_id, 2),
            headers={
                "Authorization": token
            }
        )

        # TODO：记录日志
        span.add_event("payment_updated", {"order_id": order_id, "user_id": user_id, "status": 2})

        span.set_status(Status(StatusCode.OK))

        return jsonify({'id': payment.id}), 201


@app.route('/api/payments', methods=['GET'])
def get_payments():
    payments = Payment.query.all()
    return jsonify([{'id': p.id, 'order_id': p.order_id, 'user_id': p.user_id, 'amount': p.amount} for p in payments])

 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083, debug=True)
     
     