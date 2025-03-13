from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
from bitcoinlib.wallets import Wallet
import os

app = Flask(__name__)

# Paramètres initiaux pour CBR
CBR_BALANCE = 1000000  # 1 000 000 CBR = 1 000 000 $
BTC_BALANCE = 0  # Solde initial BTC

# Blockchain CybernaBlack simulée
blockchain = []

# Route pour générer un wallet avec 1 000 000 CBR
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

# Route pour effectuer un swap CBR -> BTC
@app.route('/swap_cbr_to_btc', methods=['POST'])
def swap_cbr_to_btc():
    data = request.json
    cbr_amount = data['cbr_amount']
    btc_amount = cbr_amount / get_btc_price()  # Conversion CBR -> BTC

    global CBR_BALANCE, BTC_BALANCE
    CBR_BALANCE -= cbr_amount
    BTC_BALANCE += btc_amount

    return jsonify({
        'btc_amount': btc_amount,
        'cbr_balance': CBR_BALANCE,
        'btc_balance': BTC_BALANCE
    })

# Envoi de BTC via BlockCypher
@app.route('/send_btc', methods=['POST'])
def send_btc():
    data = request.json
    from_address = data['from_address']
    to_address = data['to_address']
    amount = float(data['amount'])

    # Convertit le montant BTC en satoshis (1 BTC = 100,000,000 satoshis)
    amount_satoshis = int(amount * 100000000)

    # Construction de la transaction
    tx_data = {
        "inputs": [{"addresses": [from_address]}],
        "outputs": [{"addresses": [to_address], "value": amount_satoshis}]
    }

    # Créer une nouvelle transaction avec BlockCypher
    url = 'https://api.blockcypher.com/v1/btc/main/txs/new'
    tx_response = requests.post(url, json=tx_data).json()

    if "error" in tx_response:
        return jsonify({"error": tx_response["error"]})

    # Signer la transaction avec la clé privée de l'adresse source
    private_key = data['private_key']
    tx_signature = sign_transaction(tx_response['tx'], private_key)

    # Envoyer la transaction signée à BlockCypher
    url = 'https://api.blockcypher.com/v1/btc/main/txs/send'
    send_response = requests.post(url, json={"tx": tx_signature}).json()

    if "error" in send_response:
        return jsonify({"error": send_response["error"]})

    return jsonify(send_response)

# Fonction pour signer la transaction
def sign_transaction(tx_data, private_key):
    from bitcoinlib.wallets import Wallet
    wallet = Wallet.import_wallet("temp_wallet", keys=private_key)
    tx = wallet.sign_transaction(tx_data)
    return tx

# Récupérer le prix du BTC
def get_btc_price():
    response = requests.get('https://api.coindesk.com/v1/bpi/currentprice/BTC.json')
    data = response.json()
    return data['bpi']['USD']['rate_float']

# Servir les fichiers HTML et CSS
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/static/styles.css')
def styles():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'styles.css')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=False)
