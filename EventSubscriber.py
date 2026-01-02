from abc import ABC, abstractmethod
import requests
import logging
import time

from Backend import StatusCode
'''
RESTFUL API - CRUD 
uniformed representations - resources as URI, not actions, interact directly with resources
stateless
cacheable
layered
client server
code on demand

payment state machine:
- created
- verified
- authorised
- settled
'''

logger = logging.getLogger(__name__)
logger.propagate = False  
handler = logging.FileHandler("logs/subscriber_logs.txt")
logger.addHandler(handler)


#Subscribers
class EventSubscriber(ABC):
    @abstractmethod
    def handle_event(self, database_server, transaction_id) -> StatusCode: 
        pass

class AnalyticsSubscriber(EventSubscriber):
    def handle_event(self, database_server, transaction_id) -> StatusCode:
        try:
            param_json = {"transaction_id": transaction_id}
            response = requests.get(f"{database_server}/txn", params=param_json)
            if response.status_code == 200:
                details = response.json()["details"]
                logger.info(f"{time.time()}: Transaction {transaction_id} logged for analytics: transaction details: {details}")
                logger.info(f"{time.time()}: Transaction {transaction_id} logged for analytics: transaction details: {details}")
                return StatusCode.SUCCESS
        except Exception as e:
            logger.error(f"{time.time()}: Error occurred logging transaction for analytics. Error {str(e)}")
        return StatusCode.FAILURE

class EmailSubscriber(EventSubscriber):
    def handle_event(self, database_server, transaction_id) -> StatusCode: 
        try:
            param_json = {"transaction_id": transaction_id}
            response = requests.get(f"{database_server}/txn", params=param_json)
            if response.status_code == 200:
                details = response.json()["details"]
                logger.info(f"{time.time()}: Transaction {transaction_id} details sent to merchant: transaction details: {details}")
                return StatusCode.SUCCESS
        except Exception as e:
            logger.error(f"{time.time()}: Error occurred sending details to merchant. Error {str(e)}")
        return StatusCode.FAILURE

class SupportSubscriber(EventSubscriber):
    def handle_event(self, database_server, transaction_id) -> StatusCode:
        try:
            param_json = {"transaction_id": transaction_id}
            response = requests.get(f"{database_server}/txn", params=param_json)
            if response.status_code == 200:
                details = response.json()["details"]
                logger.info(f"{time.time()}: Transaction {transaction_id} details sent to support personnnel: transaction details: {details}")
                print("support", )
                return StatusCode.SUCCESS
        except Exception as e:
            logger.error(f"{time.time()}: Error occurred sending details to support personnnel. Error {str(e)}")
        return StatusCode.FAILURE