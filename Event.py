from abc import ABC, abstractmethod
from enum import IntEnum

'''
payment state machine:
- checkout
- verified
- checked
- authorised
- fulfilled
- rejected
'''
class TransactionStatus(IntEnum):
    CREATED = 0
    VERIFIED = 1
    CHECKED = 2
    AUTHORISED = 3
    FULFILLED = 4
    REJECTED = 5
    TERMINATED = 6

#Events - immutable, only logging the status
class Event(ABC):
    def __init__(self, transaction_id):
        self.transaction_id = transaction_id
    
    def get_transaction_id(self):
        return self.transaction_id
    
    @abstractmethod
    def get_status(self):
        pass

    def to_string(self):
        return {"id": self.transaction_id, "status": self.get_status()}

class CreatedEvent(Event):
    def __init__(self, transaction_id:str):
        super().__init__(transaction_id)
        self.status = TransactionStatus.CREATED
    
    def get_status(self):
        return self.status

    
class VerifiedEvent(Event):
    def __init__(self, transaction_id:str):
        super().__init__(transaction_id)
        self.status = TransactionStatus.VERIFIED
    
    def get_status(self):
        return self.status
    
    
class CheckedEvent(Event):
    def __init__(self, transaction_id:str):
        super().__init__(transaction_id)
        self.status = TransactionStatus.CHECKED
    
    def get_status(self):
        return self.status


class AuthorisedEvent(Event):
    def __init__(self, transaction_id:str):
        super().__init__(transaction_id)
        self.status = TransactionStatus.AUTHORISED
    
    def get_status(self):
        return self.status


class FulfilledEvent(Event):
    def __init__(self, transaction_id:str):
        super().__init__(transaction_id)
        self.status = TransactionStatus.FULFILLED
    
    def get_status(self):
        return self.status


class RejectedEvent(Event):
    def __init__(self, transaction_id:str):
        super().__init__(transaction_id)
        self.status = TransactionStatus.REJECTED
    
    def get_status(self):
        return self.status


class TerminatedEvent(Event):
    def __init__(self, transaction_id:str):
        super().__init__(transaction_id)
        self.status = TransactionStatus.TERMINATED
    
    def get_status(self):
        return self.status