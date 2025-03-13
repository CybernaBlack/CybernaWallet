from flask import Flask, request, jsonify, render_template
import requests
from bitcoinlib.wallets import Wallet
import os
import uuid  # Ajout du module uuid pour générer des noms uniques

app = Flask(__name__)

# Paramètres initiaux pour CBR
CBR_BALANCE = 1000000  # 1 000 000 CBR = 1 000 000 $
BTC_BALANCE = 0  # Solde initial BTC

# Taux de change USD -> EUR
USD_TO_EUR = 0.94

# Blockchain CybernaBlack simulée
blockchain = []

# Route pour générer un wallet avec 1 000 000 CBR
@app.route('/generate_wallet', methods=['POST'])
def generate_wallet():
    try:
        # Génération d'un identifiant unique pour chaque wallet
        wallet_name = 'CybernaWallet_' + str(uuid.uuid4())

        wallet = Wallet.create(wallet_name, network='bitcoin')  # Utilisation du nom unique
        private_key = wallet.get_key().key_private.hex()  # Conversion en hexadécimal
        public_address = wallet.get_key().address

        add_block_to_blockchain(public_address, CBR_BALANCE)
        return jsonify({
            'private_key': private_key,  # Renvoi de la clé privée en hexadécimal
            'public_address': public_address,
            'cbr_balance': CBR_BALANCE,
            'btc_balance': BTC_BALANCE
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    try:
        cbr_amount = float(data['cbr_amount'])  # Conversion en float pour éviter l'erreur TypeError
        btc_price = get_btc_price()
        if btc_price == 0:
            return jsonify({'error': 'Impossible de récupérer le prix du BTC'}), 500

        btc_amount = cbr_amount / btc_price  # Conversion CBR -> BTC

        global CBR_BALANCE, BTC_BALANCE
        CBR_BALANCE -= cbr_amount
        BTC_BALANCE += btc_amount

        return jsonify({
            'btc_amount': btc_amount,
            'cbr_balance': CBR_BALANCE,
            'btc_balance': BTC_BALANCE
        })
    except ValueError:
        return jsonify({'error': 'Montant CBR invalide'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Envoi de BTC via BlockCypher
@app.route('/send_btc', methods=['POST'])
def send_btc():
    data = request.json
    try:
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Récupérer le prix du BTC
def get_btc_price():
    try:
        response = requests.get('https://api.coindesk.com/v1/bpi/currentprice/BTC.json')
        data = response.json()
        return data['bpi']['USD']['rate_float']
    except Exception as e:
        return 0  # En cas d'erreur, on retourne 0 pour éviter des plantages

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
