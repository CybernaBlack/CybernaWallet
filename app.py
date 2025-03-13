from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
from bitcoinlib.wallets import Wallet
import os

app = Flask(__name__)

# Paramètres initiaux pour CBR
CBR_BALANCE = 1000000  # 1 000 000 CBR = 1 000 000 $
BTC_BALANCE = 0  # Solde initial BTC

# Taux de change USD -> EUR
USD_TO_EUR = 0.94

# Blockchain CybernaBlack simulée
blockchain = []

# Création de wallet avec 1 000 000 CBR attribués
@app.route('/generate_wallet', methods=['POST'])
def generate_wallet():
    wallet = Wallet.create('CybernaWallet', keys='create')
    private_key = wallet.get_key().key_private
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

# Swap CBR -> BTC
@app.route('/swap_cbr_to_btc', methods=['POST'])
def swap_cbr_to_btc():
    data = request.json
    cbr_amount = data['cbr_amount']
    btc_amount = cbr_amount / get_btc_price()

    return jsonify({
        'btc_amount': btc_amount,
        'cbr_balance': CBR_BALANCE - cbr_amount,
        'btc_balance': BTC_BALANCE + btc_amount
    })

# Envoi de BTC via BlockCypher
@app.route('/send_btc', methods=['POST'])
def send_btc():
    data = request.json
    from_address = data['from_address']
    to_address = data['to_address']
    amount = int(float(data['amount']) * 100000000)  # Converti BTC en satoshis

    tx_data = {
        "inputs": [{"addresses": [from_address]}],
        "outputs": [{"addresses": [to_address], "value": amount}]
    }

    url = 'https://api.blockcypher.com/v1/btc/main/txs/new'
    tx_response = requests.post(url, json=tx_data).json()

    return jsonify(tx_response)

# Récupérer le prix du BTC
def get_btc_price():
    response = requests.get('https://api.coindesk.com/v1/bpi/currentprice/BTC.json')
    data = response.json()
    return data['bpi']['USD']['rate_float']

# Servir les fichiers HTML et CSS
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/styles.css')
def styles():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'styles.css')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
