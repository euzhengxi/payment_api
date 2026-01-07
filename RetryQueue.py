from collections import deque
import requests

from Backend import *
from Event import FulfilledEvent

logger = logging.getLogger(__name__)
logger.propagate = False  
handler = logging.FileHandler("logs/failed_txn_logs.txt")
logger.addHandler(handler)

class FailedTransaction :
    def __init__(self, transaction_id, webhook):
        self.id = transaction_id
        self.webhook = webhook

class RetryQueue:
    def __init__(self, database_server, broker):
        self.queue: deque[FailedTransaction] = deque()
        self.initialise_retry_queue()
        self.database_server = database_server
        self.event_broker = broker
    
    def initialise_retry_queue(self):
        try:
            with open("databases/retry_queue.json") as file:
                txns = json.load(file)
        except Exception as e:
            logger.critical(f"Error initialising retry queue: {e}")
        else:
            for txn in txns:
                self.enqueue(txn["id"], txn["webhook"])
    
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
                logger.warning(f"Attempt {retry_attempt + 1}: Error sending updates to client")
                if retry_attempt != 2:
                    delay = random.randint(0, 2 ** (retry_attempt+ 1))
                    logger.warning(f"delaying for {delay} seconds before retrying")
                    time.sleep(delay)
                else:
                    logger.warning("All attempts updating the client failed")
                logger.warning(e)
    
    def handle_shutdown(self):
        if self.queue:
            queue = []
            for txn in self.queue:
                queue.append({"id": txn.id, "webhook":txn.webhook})
            
            try:
                with open("databases/retry_queue.json") as file:
                    json.dump(queue, file, indent=4)
            except Exception as e:
                logger.critical(f"Error flushing retry events to database: {e}")
            else:
                logger.info("Failed txns flushed to database")
        else:
            logger.info("Retry queue is empty. No data is flushed")

    def run(self, shutdown_event):
        while not shutdown_event.is_set():
            for _ in range(len(self.queue)):
                txn = self.queue.popleft()
                transaction_id = txn.id
                webhook = txn.webhook
                status = self.fulfill_transaction(transaction_id)
                if status == StatusCode.SUCCESS:
                    self.event_broker.publish_event(FulfilledEvent(transaction_id))
                    self.send_updates(transaction_id, webhook)
                else:
                    self.enqueue(transaction_id, webhook)
                time.sleep(5)
        self.handle_shutdown()
        
        