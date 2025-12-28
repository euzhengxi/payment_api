import json
import pathlib
import logging
from flask import Flask, request

from CustomExceptions import DirtyCacheError

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/db_logs.txt', level=logging.INFO)

#routing functions
app = Flask(__name__)
@app.route("/v1/status", methods=["GET"])
def get_database_status():
    if database.data:
        return {"status": "running"}, 200
    return {"status": "internal server error"}, 500

@app.route("/v1/txn", methods=["POST"])
def log_transaction():
    info = request.get_json()
    transaction_id = database.log_transaction(payer=info["payer"], payee=info["payee"], amount=info["amount"], timestamp=info["timestamp"])
    if transaction_id != None:
        return {"message": "Transaction logged", "transaction_id": transaction_id}, 200
    return {"message": "Duplicate transaction id", "transaction_id": None}, 500

@app.route("/v1/txn", methods=["GET"])
def get_transaction_details():
    transaction_id= request.args.get("transaction_id")
    details = database.get_transaction(transaction_id=transaction_id)
    if details != None:
        return {"message": "transaction found", "details":details}, 200
    return {"message": "transaction_id not found", "details": None}, 500

@app.route("/v1/txn_status", methods=["POST"])
def log_transaction_status():
    info = request.get_json()
    status = database.log_status(transaction_id=info["transaction_id"], status=info["status"])
    if status == StatusCode.SUCCESS:
        return {"message": "Transaction status logged"}, 200
    return {"message": "Transaction_id not found"}, 500

class StatusCode:
    SUCCESS = 0
    FAILURE = 1

class Database:
    def __init__(self, database_file):
        self.database_file = database_file
        try:
            with open (database_file, "r") as file:
                self.data = json.load(file)
            file_path = pathlib.Path(database_file)
            timestamp = file_path.stat().st_mtime
            if self.data["last_modified"] != "new" and self.data["last_modified"] != timestamp:
                raise DirtyCacheError
            
        except DirtyCacheError:
            logger.error("Unauthorised amendments to transaction data")
            raise
        except FileNotFoundError:
            logger.error(f"Error: The file {database_file} was not found.")
            raise
        except Exception as e:
            logger.error(f"Error opening file: {e}")
            raise
        else:
            logger.info(f"Database initialised at {timestamp}")

    def _compute_transaction_id(self, payer, payee, amount, timestamp):
        return f"{payer}-{payee}-{amount}-{timestamp}"

    def log_transaction(self, payer, payee, amount, timestamp):
        transaction_id = self._compute_transaction_id(payer, payee, amount, timestamp)

        if transaction_id in self.data:
            logger.warning(f"Duplicate transaction ignored. id:{transaction_id}, payer:{payer}, payee:{payee}, amount:{amount}, timestamp:{timestamp}")
            return None
        
        details = dict()
        details["payer"] = payer
        details["payee"] = payee
        details["amount"] = amount
        details["timestamp"] = timestamp
        self.data[transaction_id]= dict()
        self.data[transaction_id]["details"] = details

        try:
            with open(self.database_file, "w") as file:
                json.dump(self.data, file, indent=4)
        except Exception as e:
            pass
        else:
            return transaction_id
        return None

    def log_status(self, transaction_id, status) -> StatusCode:
        if self.data and transaction_id in self.data:
            self.data[transaction_id]["status"] = status
            try:
                with open(self.database_file, "w") as file:
                    json.dump(self.data, file, indent=4)
            except Exception as e:
                return StatusCode.FAILURE
            else:
                return StatusCode.SUCCESS
        elif self.data:
            logger.warning(f"transaction id not found in database. id: {transaction_id}")
        else:
            logger.error(f"data is not initialised.")

        return StatusCode.FAILURE

    def get_transaction(self, transaction_id):
        transaction_details = None
        if self.data and transaction_id in self.data:
            transaction_details = self.data[transaction_id]["details"]
        elif self.data:
            logger.warning(f"transaction id not found in database. id: {transaction_id}")
        else:
            logger.error(f"data is not initialised.")

        return transaction_details
        

if __name__ == "__main__":
    database = Database("databases/txn_database.json")
    app.run(port=8001)



    
    
    

        