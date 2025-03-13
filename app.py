from flask import Flask, request, jsonify, render_template
import requests
from bitcoinlib.wallets import Wallet
import os
import uuid

app = Flask(__name__)

# Paramètres initiaux pour CBR et BTC
CBR_BALANCE = 1000000  # 1 000 000 CBR = 1 000 000 $
BTC_BALANCE = 0  # Solde initial BTC

# Taux de change fixe : 1000 CBR = 1 BTC
CBR_TO_BTC_RATE = 1000

# Blockchain CybernaBlack simulée
blockchain = []

# Route pour générer un wallet avec 1 000 000 CBR
@app.route('/generate_wallet', methods=['POST'])
def generate_wallet():
    wallet_name = 'CybernaWallet_' + str(uuid.uuid4())

    wallet = Wallet.create(wallet_name, network='bitcoin')
    private_key = wallet.get_key().key_private.hex()
    public_address = wallet.get_key().address
    
    add_block_to_blockchain(public_address, CBR_BALANCE)
    return jsonify({
        'private_key': private_key,
        'public_address': public_address,
        'cbr_balance': CBR_BALANCE,
        'btc_balance': BTC_BALANCE
    })

# Ajout d'un bloc à la blockchain CybernaBlack
def add_block_to_blockchain(address, amount):
    block = {
        'from': 'CybernaBlack System',
        'to': address,
        'amount': amount,
        'transaction_type': 'mint'
    }
    blockchain.append(block)

# Route pour effectuer un swap CBR -> BTC avec un taux fixe
@app.route('/swap_cbr_to_btc', methods=['POST'])
def swap_cbr_to_btc():
    data = request.json
    cbr_amount = float(data['cbr_amount'])

    if cbr_amount > CBR_BALANCE:
        return jsonify({'error': 'Fonds CBR insuffisants'}), 400

    btc_amount = cbr_amount / CBR_TO_BTC_RATE

    global CBR_BALANCE, BTC_BALANCE
    CBR_BALANCE -= cbr_amount
    BTC_BALANCE += btc_amount

    return jsonify({
        'btc_amount': f"{btc_amount:.8f}",
        'cbr_balance': CBR_BALANCE,
        'btc_balance': BTC_BALANCE
    })

# Envoi de BTC via BlockCypher
@app.route('/send_btc', methods=['POST'])
def send_btc():
    data = request.json
    from_address = data['from_address']
    to_address = data['to_address']
    amount = int(float(data['amount']) * 100000000)  # Convertit BTC en satoshis

    tx_data = {
        "inputs": [{"addresses": [from_address]}],
        "outputs": [{"addresses": [to_address], "value": amount}]
    }

    url = 'https://api.blockcypher.com/v1/btc/main/txs/new'
    tx_response = requests.post(url, json=tx_data).json()

    return jsonify(tx_response)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
