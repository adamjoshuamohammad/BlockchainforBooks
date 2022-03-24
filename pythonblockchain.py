import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.new_block(prev_hash='1', proof=100)
        
    # #Create the genesis block
    # def create_genesis_block(self):
    #     self.new_block(previous_hash=1, proof=100)
    
    def new_block(self, proof, prev_hash):
        '''
        Create a new block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        '''

        block = {
            'index': len(self.chain)+1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'prev_hash': prev_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, isbn):
        '''
        Creates a new transaction to go into the next mined Block
        :param from: <str> Address of the Sender
        :param to: <str> Address of the Recipient
        :param isbn: <int> ISBN of Book
        :return: <int> The index of the Block that will hold this transaction
        '''
        self.current_transactions.append({
            'sender':sender,
            'recipient':recipient,
            'isbn':isbn,
        })

        return self.last_block['index']+1

    @staticmethod
    def hash(block):
        '''
        Creates a SHA-256 hash of a Block
        :param block: <dict> Block
        :return: <str>
        '''
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        #returns the last block in the chain
        return self.chain[-1]

    def new_transaction(self, sender, recipient, isbn):
        '''
        Creates a new transaction to fo into the next mined Block
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param isbn: <int> ISBN of book
        :return: <int> The index of the Block that will hold this transaction
        '''

        self.current_transactions.append({
            'sender':sender,
            'recipient':recipient,
            'isbn':isbn,
        })

        return self.last_block['index']+1


    def proof_of_work(self, last_block):
        '''
        Simple Proof of Work Algorithm:
        - Find a number p' such that hash(pp) contains 4 leading zeroes, where p is the previous p'
        - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return: <int>
        '''

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        '''
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        '''

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4]=="0000"

#Instantiating the Blockchain
app = Flask(__name__)

node_identifier = str(uuid4()).replace('-','')

blockchain = Blockchain()

@app.route('/chain', methods=['GET'])
def full_chain():
    response={
        'chain':blockchain.chain,
        'length':len(blockchain.chain)
    }
    return jsonify(response), 200

if __name__ == '_main_':
    app.run(host='0.0.0.0', port=5000)

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values=request.get_json()

    #Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'isbn']
    if not all(k in values for k in required):
        return 'Missing values', 400
    
    #Create a new transaction
    index=blockchain.new_transaction(values['sender'], values['recipient'], values['isbn'])

    response = {'message': 'Transaction will be added to Block {}'.format(index)}
    return jsonify(response), 201

@app.route('/mine', methods=['GET'])
def mine():

    #We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    #Reward for mining (to be removed)
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        isbn=0,
    )

    #Forge the new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'prev_hash': block['prev_hash'],
    }

    return jsonify(response), 200
