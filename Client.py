import time
import requests


def create_new_transaction(arg_list:list):
    if arg_list[0] != "new":
        print("Invalid Command! Pls try again")
    else:
        request_json =  {
            "payer": arg_list[1],
            "payee": arg_list[2],
            "amount": arg_list[3],
            "timestamp": time.time()
        }
        try: 
            response = requests.post(f"{payment_api_url}/txn", json=request_json)
            if response.status_code == 200:
                transaction_id = response.json()["transaction_id"]
                print(f"Transaction: successfully captured, Details can be obtained using {transaction_id}")
            else:
                message = response.json()["message"]
                print(f"Error creating transaction. {message}")
                print("Pls try again later")
        except Exception as e:
            print("an error occurred")
            print(e)

def get_transaction_details(arg_list:list):
    if arg_list[0] != "read":
        print("Invalid Command! Pls try again")
    else:
        param_json = {"transaction_id": arg_list[1]}
        response = requests.get(f"{payment_api_url}/txn", params=param_json)
        if response == 200:
            details = response.json()["details"]
            print(f"{details}")
            #print(f"payee: {details["payee"]}")
            #print(f"amount: {details["amount"]}")
            #print(f"time transaction is fulfill: {details["timestamp"]}")
        else:
            message = response.json()["message"]
            print(message)
            print(f"Error reading. {message}")
            print("Pls try again later")

if __name__ == "__main__":
    
    payment_api_url = "http://127.0.0.1:8000/v1"

    print("Welcome to thrustworhy payment! Where trustng us is your biggest mistake!")
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