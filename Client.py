import time
import requests
import random
from flask import Flask, request
import threading

from CustomExceptions import TransactionRegistrationError, TransactionCreationError

app = Flask(__name__)
@app.route("/v1/txn", methods=["POST"])
def get_updates():
    response = request.get_json()
    transaction_id = response["transaction_id"]
    print(f"transaction {transaction_id} fulfilled")
    get_transaction_details(["read", transaction_id])
    return {"message":"update received"}, 200

def run_webhook_server():
    app.run(port=9000)

def create_new_transaction(arg_list:list):
    if arg_list[0] != "new":
        print("Invalid Command! Pls try again")
    else:
        request_json =  {
            "payer": arg_list[1],
            "payee": arg_list[2],
            "amount": arg_list[3],
        }

        for retry_attempt in range(3):
            try: 
                param_json = {"nonce": sessionID}
                response = requests.get(f"{payment_api_url}/token", params=param_json)
                if response.status_code == 200:
                    token = response.json()["token"]
                    print("Transaction successfully registered")
                else:
                     raise TransactionRegistrationError
            
            except Exception as e:
                message = response.json()["message"]
                print(f"Attempt {retry_attempt + 1}: Error registering transaction. {message}")
                if retry_attempt != 2:
                    delay = random.randint(0, 2 ** (retry_attempt + 1))
                    print(f"delaying for {delay} seconds before retrying")
                    print()
                    time.sleep(delay)
                else:
                    print("Error registering transaction after 3 tries, Please try again later")

            else:

                request_json["token"] = token
                request_json["webhook"] = "http://127.0.0.1:9000/v1"
                try: 
                    response = requests.post(f"{payment_api_url}/txn", json=request_json)
                    if response.status_code == 200:
                        transaction_id = response.json()["transaction_id"]
                        print(f"Transaction: successfully captured, Details can be obtained using {transaction_id}")
                        break
                    elif response.status_code == 202:
                        message = response.json()["message"]
                        transaction_id = response.json()["transaction_id"]
                        print(f"Transaction: {transaction_id} fulfillment incomplete. Please check back later")
                        break
                    else:
                        raise TransactionCreationError
                except Exception as e:
                    message = response.json()["message"]
                    print(f"Attempt {retry_attempt + 1}: Error creating transaction. {message}")
                    
                    if retry_attempt != 2:
                        delay = random.randint(0, 2 ** (retry_attempt + 1))
                        print(f"delaying for {delay} seconds before retrying")
                        print()
                        time.sleep(delay)
                    else:
                        print("Error creating transaction after 3 tries, Please try again later")
                        print()
            
            

def get_transaction_details(arg_list:list):
    if arg_list[0] != "read":
        print("Invalid Command! Pls try again")
    else:
        param_json = {"transaction_id": arg_list[1]}
        try:
            response = requests.get(f"{payment_api_url}/txn", params=param_json)
            if response.status_code == 200:
                details = response.json()
                print(f'payee: {details["payee"]}')
                print(f'amount: {details["amount"]}')
                print(f'time transaction is fulfilled: {details["timestamp"]}')
        except Exception as e:
            message = response.json()["message"]
            print(message)
            print(f"Error reading. {message}")
            print("Pls try again later")

if __name__ == "__main__":

    #start flask in background
    threading.Thread(target=run_webhook_server,daemon=True).start()
    
    payment_api_url = "http://127.0.0.1:8000/v1"

    print("Welcome to thrustworhy payment! Where trustng us is your biggest mistake!")
    sessionID = f"{int(time.time()) + random.randint(0, 10 ** 10)}"

    while True:
        
        print("To create a new transaction. Input the following: ")
        print("new <payer> <payee> <amount>")
        print()
        print("To get details about a previous transaction. Input the following: ")
        print("read <transaction_id>")
        print()

        arguments = input()
        arg_list = arguments.split(" ")
        if len(arg_list) == 4:
            create_new_transaction(arg_list)
        else:
            get_transaction_details(arg_list)