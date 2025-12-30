from flask import Flask, request
import json
import sys
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import requests
import argparse
import logging
import threading

from Event import * 
from EventSubscriber import *
from Backend import *
from CustomExceptions import LoggingTransactionError, LoggingTransactionStatusError

#read up more on usage of logger

'''
external interface: RESTFUL API
internal interface: 
    - critical path: synchronous
    - side effects: asynchronous

Rough payment workflow
1. transaction verification - card number, expiry date and cvc
2. fraud detection - transaction details, address, duplicate transactions
3. notifying issuer using card network (event driven architecture?)
4. updating customers and business
5. releasing funds to business 
'''
logger = logging.getLogger()
logging.basicConfig(filename='logs/api_logs.txt', level=logging.INFO)

def set_up_parser():
    parser = argparse.ArgumentParser(
                    prog="payment api",
                    description="A simple payment api program using microservices and EDA",
                    epilog="...")
    parser.add_argument("-database_server", help="url of database server")
    parser.add_argument("-issuer_server", help="url of issuer server")
    return parser

def check_database_availability():
    response = requests.get(f"{database_server}/status")
    if response.status_code == 200:
        return StatusCode.SUCCESS
    return StatusCode.FAILURE

#endpoint setup
app = Flask(__name__)
@app.route("/v1/status", methods=["GET"])
def get_server_status():
    return {"status": "running"}, 200

@app.route("/v1/token", methods=["GET"])
def compute_transaction_token():
    nonce = request.args.get("nonce")
    token = compute_token(nonce)
    return {"message": "Token successfully registered", "token":token}, 200

@app.route("/v1/txn", methods=["POST"])
def create_transaction():
    info = request.get_json()
    payer, payee = info["payer"], info["payee"]
    amount = float(info["amount"])
    token = info["token"]
    #synchronous critical path, asynchronous side effects
    transaction_json = {
        "payer": payer,
        "payee": payee,
        "amount": amount,
        "token": token
    }

    #logging transaction with retries
    transaction_id = None
    for retry_attempt in range(3):
        try:
            response = requests.post(f'{database_server}/txn', json=transaction_json)
            if (response.status_code == 200):
                transaction_id = response.json()["transaction_id"]
                break
            else:
                raise LoggingTransactionError
        except Exception as e:
            if retry_attempt != 2: 
                delay = random.randint(0, 2 ** retry_attempt)
                logger.warning(f"Attempt {retry_attempt}: Error logging transaction.")
                print(f"delaying for {delay} seconds before retying")
                time.sleep(delay)
            logger.warning(f"Error logging transaction in database: {e}")

    if transaction_id == None:
        logger.warning(f"{time.time()}: Error creating transaction. Details: payer:{payer}, payee:{payee}, amount:{amount}, token:{token}")
        return {"message": "Failure creating transaction, please try again later", "transaction_id":None, "details":None}, 500


    http_response = {
        "message": "",
        "transaction_id": transaction_id, 
        "details": {
            "payer": payer, 
            "payee": payee, 
            "amount": amount,
            "token": token
        }
    }
    broker.publish_event(CreatedEvent(transaction_id))
        
    #verify transaction
    status = verify_transaction(payer, payee, amount)
    if status == StatusCode.FAILURE:
        broker.publish_event(RejectedEvent(transaction_id))
        http_response["message"] = "transaction verification error"
        return http_response, 500
        
    broker.publish_event(VerifiedEvent(transaction_id))

        
    #check for fraud
    status = check_fraud(payer, payee, amount)
    if status == StatusCode.FAILURE:
        broker.publish_event(RejectedEvent(transaction_id))
        http_response["message"] = "transaction fraud error"
        return http_response, 500

    broker.publish_event(CheckedEvent(transaction_id))

    #get authorisation from issuer
    status = get_authorisation(payer, payee, amount, issuer_server)
    if status == StatusCode.FAILURE:
        broker.publish_event(RejectedEvent(transaction_id))
        http_response["message"] = "transaction authorisation error"
        return http_response, 500 
        
    broker.publish_event(AuthorisedEvent(transaction_id))
        
    #update merchant's account
    status = fulfill_transaction(payer, payee, amount)
    if status == StatusCode.FAILURE:
        broker.publish_event(RejectedEvent(transaction_id))
        http_response["message"] = "transaction fulfillment error"
        return http_response, 500
    broker.publish_event(FulfilledEvent(transaction_id))

    http_response["message"] = "transaction completed"
    return http_response, 200
        

@app.route("/v1/txn", methods=["GET"])
def get_transaction_details():
    transaction_id= request.args.get("transaction_id")
    param_json = {"transaction_id": transaction_id}
    try:
        response = requests.get(f"{database_server}/txn", params=param_json)
        if response.status_code == 200:
            return response.json()["details"], 200
        else:
            raise Exception
    except Exception as e:
        return {"message": f"Error getting transaction details {e}"}, 500    

#EventBroker
class EventBroker:
    executor = ThreadPoolExecutor(max_workers=4)
    subscribers = defaultdict(list)
    event_queue: deque[Event] = deque()
    
    @classmethod
    def subscribe_to_event(cls, status: TransactionStatus, subscriber: EventSubscriber):
        try:
            if not isinstance(status, TransactionStatus):
                raise TypeError(f"event_type {status} must implement TransactionStatus")
            if not isinstance(subscriber, EventSubscriber):
                raise TypeError(f"subscriber {subscriber} must implement EventSubscriber")
        except TypeError as e:
            logger.fatal("{time.time()}: Invalid type found in event subscription. {e}")
            raise
        else:
            cls.subscribers[status].append(subscriber)

    @classmethod
    def publish_event(cls, event):
        if not isinstance(event, Event):
            logger.error(f"{time.time()}: event {event} does not implement Event")
            cls.event_queue.append(TerminatedEvent(event.get_transaction_id()))
        else:
            cls.event_queue.append(event)
    
    @classmethod
    def log_status(self, transaction_id, status):
        request_json = {"transaction_id": transaction_id, "status": status}
        for retry_attempt in range(3):
            try:
                response = requests.post(f"{database_server}/txn_status", json=request_json)
                if response.status_code == 200:
                    break
                else: 
                    raise LoggingTransactionStatusError
            except Exception as e:
                if retry_attempt != 2: 
                    delay = random.randint(0, 2 ** retry_attempt)
                    logger.warning(f"Attempt {retry_attempt}: Error logging transaction status.")
                    print(f"delaying for {delay} seconds before retying")
                    time.sleep(delay)
                logger.warning(f"Attempt {retry_attempt} at logging status({status}) of transaction ({transaction_id}). Error: {str(e)}")
    
    @classmethod
    def run(cls):
        while len(cls.event_queue) != 0:
            event = cls.event_queue.popleft()
            status = event.get_status()
            transaction_id = event.get_transaction_id()
            cls.log_status(transaction_id, status)

            #handle event
            if status in cls.subscribers:
                for subscriber in cls.subscribers[status]:
                    future = cls.executor.submit(subscriber.handle_event, transaction_id) 
                    if future.result() == StatusCode.FAILURE:
                        logger.error(f"{time.time()}: {subscriber} failed handling transaction {transaction_id} with status{status}")
                        cls.publish_event(TerminatedEvent(transaction_id))     
                    


if __name__ == "__main__":
    #set up argparser
    parser = set_up_parser()
    args = parser.parse_args()
    database_server = f"{args.database_server}/v1"
    issuer_server = f"{args.issuer_server}/v1"

    #set up webserver
    status = check_database_availability()
    if status == StatusCode.FAILURE:
        logger.fatal(f"{time.time()}: Database isnt running")
        sys.exit(1)

    #set up event broker
    broker = EventBroker()
    broker.subscribe_to_event(TransactionStatus.FULFILLED, EmailSubscriber())
    broker.subscribe_to_event(TransactionStatus.REJECTED,  AnalyticsSubscriber())
    broker.subscribe_to_event(TransactionStatus.TERMINATED, SupportSubscriber())

    threading.Thread(target=broker.run, daemon=True).start()
    app.run(port=8000)





