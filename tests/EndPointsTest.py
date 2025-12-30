import requests 
import time
import random
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Database import * 
from Event import TransactionStatus 
from Issuer import *

NUM_DATABASE_ENDPOINTS = 4
NUM_ISSUER_ENDPOINTS = 3
NUM_MAIN_ENDPOINTS = 4

class DatabaseTest:
    database_server = "http://127.0.0.1:8001/v1"

    def get_database_status(self):
        response = requests.get(f"{self.database_server}/status")
        assert response.status_code == 200

    def log_transaction(self):
        request_json = {
            "payer": "0000111122223333", 
            "payee": "0000222233331111",
            "amount": 10, 
            "token": f"{int(time.time()) + random.randint(0, 10 ** 10)}"
        }
        response = requests.post(f"{self.database_server}/txn", json=request_json)
        assert response.status_code == 200

        return response.json()["transaction_id"]
    
    def get_transaction_details(self):
        transaction_id = self.log_transaction()
        param_json = {"transaction_id": transaction_id}
        response = requests.get(f"{self.database_server}/txn", params=param_json)
        assert response.status_code == 200
        assert response,json()["payer"] == "0000111122223333" 
        assert response,json()["payee"] == "0000222233331111"
        assert response,json()["amount"] == 100

    def log_transaction_status(self):
        transaction_id = self.log_transaction()
        request_json = {
            "transaction_id": transaction_id,
            "status": TransactionStatus.FULFILLED 
        }
        response = requests.post(f"{self.database_server}/txn_status", json=request_json)
        assert response.status_code == 200
    
    def run(self):
        self.get_database_status()
        self.log_transaction()
        self.get_transaction_details()
        self.log_transaction_status()
        print(f"{NUM_DATABASE_ENDPOINTS} endpoints in Database are working")

class IssuerTest:
    server = "http://127.0.0.1:8002/v1"

    def get_status(self):
        response = requests.get(f"{self.server}/status")
        assert response.status_code == 200
    
    def create_user(self):
        request_json = {"user": "0000111122223333"}
        response = requests.post(f"{self.server}/user", json=request_json)
        assert response.status_code == 200

    def create_transaction(self):
        request_json = {
            "payer": "0000111122223333", 
            "payee": "0000222233331111",
            "amount": 10
        }
        response = requests.post(f"{self.server}/txn", json=request_json)
        assert response.status_code == 200
    
    def run(self):
        self.get_status()
        self.create_user()
        self.create_transaction()
        print(f"{NUM_ISSUER_ENDPOINTS} endpoints in Issuer are working")


class MainTest:
    server = "http://127.0.0.1:8000/v1"

    def get_status(self):
        response = requests.get(f"{self.server}/status")
        assert response.status_code == 200
    
    def compute_transaction_token(self):
        sessionID = f"{int(time.time()) + random.randint(0, 10 ** 10)}"
        response = requests.get(f"{self.server}/token", params={"nonce": sessionID})
        assert response.status_code == 200
        return response.json()["token"]

    def create_transaction(self):
        token = self.compute_transaction_token()

        request_json = {
            "payer": "0000111122223333", 
            "payee": "0000222233331111",
            "amount": 10,
            "token": token,
            "webhook": "http://127.0.0.1:9000/v1"
        }

        response = requests.post(f"{self.server}/txn", json=request_json)
        assert response.status_code == 200
        return response.json()["transaction_id"]
    
    def get_transaction(self):
        transaction_id = self.create_transaction()
        param_json = {"transaction_id": transaction_id}
        response = requests.get(f"{self.server}/txn", params=param_json)
        assert response.status_code == 200
        assert response.json()["payer"] == "0000111122223333"
        assert response.json()["payee"] == "0000222233331111"
        assert response.json()["amount"] == 10
    

    def run(self):
        self.get_status()
        self.compute_transaction_token()
        self.create_transaction()
        self.get_transaction()
        print(f"{NUM_MAIN_ENDPOINTS} endpoints in main are working")

if __name__ == "__main__":
    databaseTest = DatabaseTest()
    issuerTest = IssuerTest()
    mainTest = MainTest()
    
    databaseTest.run()
    issuerTest.run()
    mainTest.run()