import logging
import json
import time
import requests
import random

logger = logging.getLogger(__name__)

class StatusCode:
    SUCCESS = 0
    FAILURE = 1

def compute_token(nonce):
    return f"{int(nonce) - random.randint(0, 10 ** 10)}"


def verify_transaction(payer:str, payee:str, amount:float) -> StatusCode: 
    for char in payer:
        if not char.isdigit():
            return StatusCode.FAILURE
            
    for char in payee:
        if not char.isdigit():
            return StatusCode.FAILURE
            
    if amount <= 0 :
        return StatusCode.FAILURE
    
    return StatusCode.SUCCESS


def check_fraud(payer:str, payee:str, amount:float) -> StatusCode: 
    SUSPICIOUS_ORGANISATIONS = ["1234111122223333"]
    if (payer or payee) in SUSPICIOUS_ORGANISATIONS:
        return StatusCode.FAILURE
    return StatusCode.SUCCESS


def get_authorisation(payer:str, payee:str, amount:float, issuer_server:str) -> StatusCode:         
    
    transaction_json = {
        "payer": payer,
        "payee": payee, 
        "amount": amount
    }

    for retry_attempt in range(3):
        try:
            response = requests.post(f"{issuer_server}/txn", json=transaction_json)
        except Exception as e:
            logger.warning(f"Attempt {retry_attempt + 1}: Error getting transaction authorised.")
            logger.warning(e)
            if retry_attempt != 2: 
                delay = random.randint(0, 2 ** (retry_attempt+ 1))
                logger.warning(f"delaying for {delay} seconds before retrying")
                time.sleep(delay)
            else:
                logger.warning("All attempts getting authorisation failed")
        else:
            if response.status_code == 200:
                return StatusCode.SUCCESS
    
    return StatusCode.FAILURE

def fulfill_transaction(transaction_id, payer, payee, amount:float) -> StatusCode:
    merchant_database = "databases/merchant_database.json"
    
    try:
        with open(merchant_database, "r") as file:
            data = json.load(file)
            data[payee]["balance"] += amount
            data[payee]["transaction"].append((time.time(), payer, amount))

        with open(merchant_database, "w") as file:
            json.dump(data, file, indent=4)
    except FileNotFoundError as e:
        logger.fatal(f"{time.time()}: Merchant database missing")
    except ValueError as e:
        logger.fatal(f"{time.time()} Merchant database is corrupted. {e}")    
    else:
        logger.info(f"transaction ({transaction_id}) logged")
        return StatusCode.SUCCESS
    return StatusCode.FAILURE