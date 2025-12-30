from collections import deque
import requests

from Backend import *
from Event import FulfilledEvent

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/failed_txn_logs.txt', level=logging.INFO)

class FailedTransaction :
    def __init__(self, transaction_id, webhook):
        self.id = transaction_id
        self.webhook = webhook

class RetryQueue:
    def __init__(self, database_server, broker):
        self.queue: deque[FailedTransaction] = deque()
        self.database_server = database_server
        self.event_broker = broker
    
    def enqueue(self, transaction_id, webhook):
        txn = FailedTransaction(transaction_id, webhook)
        self.queue.append(txn)
    
    def fulfill_transaction(self, transaction_id):
        response = requests.get(f"{self.database_server}/txn", params={"transaction_id": transaction_id})
        if response.status_code == 200:
            details = response.json()["details"]
            status = fulfill_transaction(details["payer"], details["payee"], details["amount"])
            return status
        return StatusCode.FAILURE

    def send_updates(self, transaction_id, webhook):
        request_json = {
            "transaction_id": transaction_id,
            "message": "transaction completed"
        }

        for retry_attempt in range(3):
            try:
                response = requests.post(f"{webhook}/txn", json=request_json)
                if response.status_code == 200:
                    break
                else:
                    raise Exception
                
            except Exception as e:
                delay = random.randint(0, 2 ** retry_attempt)
                logger.warning(f"Attempt {retry_attempt}: Error sending updates to client")
                print(f"delaying for {delay} seconds before retying")
                print()
                time.sleep(delay)
                if retry_attempt == 2:
                    logger.warning("All attempts updating the client failed")
                logger.warning(e)


    def run(self):
        while True:
            for _ in range(len(self.queue)):
                txn = self.queue.popleft()
                print(txn)
                transaction_id = txn.id
                webhook = txn.webhook
                status = self.fulfill_transaction(transaction_id)
                if status == StatusCode.SUCCESS:
                    self.event_broker.publish_event(FulfilledEvent(transaction_id))
                    self.send_updates(transaction_id, webhook)
                else:
                    self.enqueue(transaction_id, webhook)
                time.sleep(5)