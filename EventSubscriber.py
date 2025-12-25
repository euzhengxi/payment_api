from abc import ABC, abstractmethod
import requests
import logging
import datetime

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

#Subscribers
class EventSubscriber(ABC):
    @abstractmethod
    def handle_event(self, database_server, transaction_id) -> StatusCode: 
        pass

class AnalyticsSubscriber(EventSubscriber):
    def handle_event(self, database_server, transaction_id) -> StatusCode:
        try:
            response = requests.get(f"{database_server}/txn/{transaction_id}")
            if response.status_code == 200:
                details = response.json()["details"]
                #add transaction details for analytics
                logger.info(f"{time.time()}: transaction logged for analytics: transaction details: {details}")
                #add transaction details for fraud analysis
                logger.info(f"{time.time()}: transaction logged for analytics: transaction details: {details}")
                return StatusCode.SUCCESS
        except Exception as e:
            logger.error(f"{time.time()}: error occurred logging transaction for analytics. Error {str(e)}")
        return StatusCode.FAILURE

class EmailSubscriber(EventSubscriber):
    def handle_event(self, database_server, transaction_id) -> StatusCode: 
        try:
            response = requests.get(f"{database_server}/txn/{transaction_id}")
            if response.status_code == 200:
                details = response.json()["details"]
                #add transaction details for analytics
                logger.info(f"{time.time()}: transaction details sent to merchant: transaction details: {details}")
                return StatusCode.SUCCESS
        except Exception as e:
            logger.error(f"{time.time()}: error occurred sending details to merchant. Error {str(e)}")
        return StatusCode.FAILURE

class SupportSubscriber(EventSubscriber):
    def handle_event(self, database_server, transaction_id) -> StatusCode:
        try:
            response = requests.get(f"{database_server}/txn/{transaction_id}")
            if response.status_code == 200:
                details = response.json()["details"]
                #add transaction details for analytics
                logger.info(f"{time.time()}: transaction details sent to support personnnel: transaction details: {details}")
                return StatusCode.SUCCESS
        except Exception as e:
            logger.error(f"{time.time()}: error occurred sending details to support personnnel. Error {str(e)}")
        return StatusCode.FAILURE