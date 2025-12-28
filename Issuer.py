from flask import Flask, request
import json
import pathlib
import logging
import time

#user defined libraries
from CustomExceptions import DirtyCacheError

'''
RESTFUL API - CRUD 
uniformed representations - resources as URI, not actions, interact directly with resources
stateless
cacheable
layered
client server
code on demand

Rough payment workflow
1. transaction verification - card number, expiry date and cvc
2. fraud detection - transaction details, address, duplicate transactions
3. notifying issuer using card network (event driven architecture?)
4. updating customers and business
5. releasing funds to business 
'''
logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/issuer_logs.txt', level=logging.INFO)

class StatusCode:
    SUCCESS = 0
    FAILURE = 1


class Transaction:
    def __init__(self, payer, payee, amount):
        self.payer = payer
        self.payee = payee
        self.amount = amount
    
    def get_transaction_information(self):
        return (self.payer, self.payee, self.amount)


#endpoints
app = Flask(__name__)
@app.route("/v1/status", methods=["GET"])
def get_status():
    return {"message": "issuer running"}, 200

@app.route("/v1/txn", methods=["POST"])
def create_transaction():
    info = request.get_json()
    logger.info(f"transaction received: {info}")
    transaction = Transaction(info["payer"], info["payee"], float(info["amount"]))
    status = issuer.check_validity(transaction)
    if status == StatusCode.SUCCESS:
        issuer.authorise(transaction)
        return {"message": "transaction authorised"}, 200
    else:
        return {"message": "transaction rejected"}, 500

@app.route("/v1/user", methods=["POST"])
def create_user():
    user = request.get_json()["user"]
    status = issuer.create_user(user)
    if status == StatusCode.SUCCESS:
        logger.info(f"user {user} created by admin")
        return {"message": f"user {user} created"}, 200
    return {"message": f"user {user} not created"}, 500


class Issuer:
    def __init__(self, database_file):
        self.database_file = database_file
        self.users = self.load_user_data(database_file)
    
    def load_user_data(self, database_file):
        try:
            with open(database_file, "r") as file:
                user_data = json.load(file)
        except FileNotFoundError:
            logger.error(f"{time.time()}: Error: The file {self.database} was not found.")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"{time.time()}: Error decoding JSON: {e}")
            raise
        else:
            file_path = pathlib.Path(self.database_file)
            timestamp = file_path.stat().st_mtime
            if user_data["last_modified"] != "new" and user_data["last_modified"] != timestamp:
                logger.error(f"{time.time()}: Unauthorised amendments to user data")
                raise DirtyCacheError("Unauthorised amendments to user data")
            else:
                logger.info(f"{time.time()}: user data successfully loaded")
            return user_data
    
    def check_validity(self, transaction: Transaction) -> StatusCode:
        payer, payee, amount = transaction.get_transaction_information()
        if payer not in self.users:
            return StatusCode.FAILURE
        if self.users[payer]["balance"] < amount:
            return StatusCode.FAILURE
        return StatusCode.SUCCESS

    def authorise(self, transaction: Transaction) -> StatusCode:
        payer, payee, amount = transaction.get_transaction_information()
        self.users[payer]["balance"] -= amount
        self.users[payer]["transactions"].append((time.time(), payee, amount))
        try:
            with open(self.database_file, "w") as file:
                json.dump(self.users, file, indent=4)
        except Exception as e:
            logger.error(f"Error occurred recording transaction: {e}")
        else:
            return StatusCode.SUCCESS
        return StatusCode.FAILURE

    def create_user(self, user):
        self.users[user] = {
            "balance": 1000,
            "transactions": []
        }

        try:
            with open(self.database_file, "w") as file:
                json.dump(self.users, file, indent=4)
        except Exception as e:
            logger.error(f"Error occurred recording transaction: {e}")
        else:
            return StatusCode.SUCCESS
        return StatusCode.FAILURE



if __name__ == "__main__":
    issuer = Issuer("databases/usr_database.json")
    app.run(port=8002)
    







