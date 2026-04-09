# Web3.py — Полная документация

## Содержание

1. [Введение](#введение)
2. [Установка](#установка)
3. [Подключение к блокчейну](#подключение-к-блокчейну)
4. [Работа с аккаунтами](#работа-с-аккаунтами)
5. [Транзакции](#транзакции)
6. [Смарт-контракты](#смарт-контракты)
7. [События и логи](#события-и-логи)
8. [Работа с ENS](#работа-с-ens)
9. [Утилиты и хелперы](#утилиты-и-хелперы)
10. [Middleware](#middleware)
11. [Асинхронная работа](#асинхронная-работа)
12. [Практические примеры](#практические-примеры)
13. [Безопасность](#безопасность)
14. [Отладка и решение проблем](#отладка-и-решение-проблем)

---

## Введение

**Web3.py** — это Python-библиотека для взаимодействия с блокчейном Ethereum. Она позволяет:

- Подключаться к Ethereum-нодам (локальным или удалённым)
- Читать данные из блокчейна
- Отправлять транзакции
- Взаимодействовать со смарт-контрактами
- Работать с ENS (Ethereum Name Service)
- Подписывать сообщения и транзакции

### Архитектура Web3.py

```
┌─────────────────────────────────────────────────────────┐
│                    Ваше приложение                       │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                       Web3.py                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │  w3.eth │  │  w3.net │  │ w3.geth │  │  w3.ens │    │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      Providers                           │
│  ┌───────────┐  ┌───────────┐  ┌───────────────────┐   │
│  │ HTTPProv. │  │ WSProv.   │  │ IPCProvider       │   │
│  └───────────┘  └───────────┘  └───────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Ethereum Node                          │
│         (Geth, Infura, Alchemy, Ankr и др.)             │
└─────────────────────────────────────────────────────────┘
```

---

## Установка

### Базовая установка

```bash
pip install web3
```

### Установка с дополнительными зависимостями

```bash
# С поддержкой Tester (для тестирования)
pip install web3[tester]

# С поддержкой IPCProvider
pip install web3[ipc]

# С поддержкой WebSocket
pip install web3[websockets]

# Всё вместе
pip install web3[tester,ipc,websockets]
```

### Проверка установки

```python
import web3
print(f"Web3.py версия: {web3.__version__}")
```

### Требования

- Python 3.8+
- pip (менеджер пакетов)

---

## Подключение к блокчейну

### Типы провайдеров

Web3.py поддерживает несколько типов подключений:

| Провайдер | Описание | Использование |
|-----------|----------|---------------|
| HTTPProvider | HTTP/HTTPS подключение | Удалённые ноды (Infura, Alchemy) |
| WebSocketProvider | WebSocket подключение | Подписки на события в реальном времени |
| IPCProvider | IPC сокет | Локальные ноды |
| EthereumTesterProvider | Тестовый провайдер | Юнит-тесты |

### HTTPProvider

```python
from web3 import Web3

# Подключение к Infura
infura_url = "https://mainnet.infura.io/v3/YOUR_PROJECT_ID"
w3 = Web3(Web3.HTTPProvider(infura_url))

# Подключение к Alchemy
alchemy_url = "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"
w3 = Web3(Web3.HTTPProvider(alchemy_url))

# Подключение к локальной ноде
local_url = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(local_url))

# С дополнительными настройками
w3 = Web3(Web3.HTTPProvider(
    infura_url,
    request_kwargs={
        'timeout': 60,
        'headers': {'Authorization': 'Bearer YOUR_TOKEN'}
    }
))

# Проверка подключения
print(f"Подключено: {w3.is_connected()}")
print(f"Номер блока: {w3.eth.block_number}")
print(f"Chain ID: {w3.eth.chain_id}")
```

### WebSocketProvider

```python
from web3 import Web3

# Подключение через WebSocket
ws_url = "wss://mainnet.infura.io/ws/v3/YOUR_PROJECT_ID"
w3 = Web3(Web3.WebSocketProvider(ws_url))

# Проверка
print(f"Подключено: {w3.is_connected()}")
```

### IPCProvider (локальная нода)

```python
from web3 import Web3

# Linux/Mac
w3 = Web3(Web3.IPCProvider('/home/user/.ethereum/geth.ipc'))

# Windows
w3 = Web3(Web3.IPCProvider(r'\\.\pipe\geth.ipc'))

# Автоопределение
w3 = Web3(Web3.IPCProvider())
```

### EthereumTesterProvider (для тестов)

```python
from web3 import Web3, EthereumTesterProvider

# Создание тестовой среды
w3 = Web3(EthereumTesterProvider())

# Тестовая среда предоставляет предзаполненные аккаунты
accounts = w3.eth.accounts
print(f"Тестовые аккаунты: {accounts}")
print(f"Баланс первого аккаунта: {w3.eth.get_balance(accounts[0])} wei")
```

### Автоматическое определение провайдера

```python
from web3.auto import w3

# Web3.py попытается автоматически найти провайдер
if w3.is_connected():
    print("Автоматически подключено!")
```

### Множественные провайдеры (Fallback)

```python
from web3 import Web3
from web3.providers import HTTPProvider

def get_web3_with_fallback(providers_urls):
    """Подключение с резервными провайдерами"""
    for url in providers_urls:
        try:
            w3 = Web3(HTTPProvider(url, request_kwargs={'timeout': 10}))
            if w3.is_connected():
                print(f"Подключено к: {url}")
                return w3
        except Exception as e:
            print(f"Ошибка подключения к {url}: {e}")
    raise ConnectionError("Не удалось подключиться ни к одному провайдеру")

# Использование
providers = [
    "https://mainnet.infura.io/v3/YOUR_KEY",
    "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY",
    "https://rpc.ankr.com/eth"
]
w3 = get_web3_with_fallback(providers)
```

---

## Работа с аккаунтами

### Создание нового аккаунта

```python
from web3 import Web3
from eth_account import Account

# Генерация нового аккаунта
account = Account.create()

print(f"Адрес: {account.address}")
print(f"Приватный ключ: {account.key.hex()}")

# ВАЖНО: Никогда не показывайте приватный ключ!
# Сохраните его в безопасном месте
```

### Создание аккаунта из мнемоники (seed phrase)

```python
from eth_account import Account

# Включение поддержки мнемоник
Account.enable_unaudited_hdwallet_features()

# Генерация мнемоники
mnemonic = Account.create_with_mnemonic()
account = mnemonic[0]
seed_phrase = mnemonic[1]

print(f"Мнемоника: {seed_phrase}")
print(f"Адрес: {account.address}")

# Восстановление из мнемоники
restored_account = Account.from_mnemonic(seed_phrase)
print(f"Восстановленный адрес: {restored_account.address}")

# Получение нескольких адресов из одной мнемоники (HD Wallet)
for i in range(5):
    path = f"m/44'/60'/0'/0/{i}"
    acc = Account.from_mnemonic(seed_phrase, account_path=path)
    print(f"Аккаунт {i}: {acc.address}")
```

### Импорт аккаунта из приватного ключа

```python
from eth_account import Account

# Из hex строки
private_key = "0x4c0883a69102937d623212..."  # Ваш приватный ключ
account = Account.from_key(private_key)

print(f"Адрес: {account.address}")
```

### Работа с Keystore файлами

```python
from eth_account import Account
import json

# Создание keystore файла
account = Account.create()
keystore = Account.encrypt(account.key, "your_password")

# Сохранение в файл
with open('keystore.json', 'w') as f:
    json.dump(keystore, f)

# Загрузка из keystore файла
with open('keystore.json', 'r') as f:
    keystore = json.load(f)
    
private_key = Account.decrypt(keystore, "your_password")
account = Account.from_key(private_key)
print(f"Восстановленный адрес: {account.address}")
```

### Проверка баланса

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_KEY"))

address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # vitalik.eth

# Баланс в Wei
balance_wei = w3.eth.get_balance(address)

# Баланс в Ether
balance_eth = w3.from_wei(balance_wei, 'ether')

print(f"Баланс: {balance_wei} Wei")
print(f"Баланс: {balance_eth} ETH")

# Баланс на определённом блоке
balance_at_block = w3.eth.get_balance(address, block_identifier=15000000)
print(f"Баланс на блоке 15000000: {w3.from_wei(balance_at_block, 'ether')} ETH")
```

### Получение количества транзакций (nonce)

```python
address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

# Количество отправленных транзакций
nonce = w3.eth.get_transaction_count(address)
print(f"Количество транзакций: {nonce}")

# Pending nonce (включая незамайненные транзакции)
pending_nonce = w3.eth.get_transaction_count(address, 'pending')
print(f"Pending nonce: {pending_nonce}")
```

### Валидация адресов

```python
from web3 import Web3

# Проверка формата адреса
address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
print(f"Валидный адрес: {Web3.is_address(address)}")

# Проверка checksum адреса
print(f"Checksum валиден: {Web3.is_checksum_address(address)}")

# Конвертация в checksum адрес
lower_address = address.lower()
checksum_address = Web3.to_checksum_address(lower_address)
print(f"Checksum адрес: {checksum_address}")
```

---

## Транзакции

### Типы транзакций в Ethereum

| Тип | Описание | EIP |
|-----|----------|-----|
| Legacy (Type 0) | Старый формат с gasPrice | - |
| Access List (Type 1) | С access list | EIP-2930 |
| EIP-1559 (Type 2) | С maxFeePerGas и maxPriorityFeePerGas | EIP-1559 |

### Отправка ETH (EIP-1559)

```python
from web3 import Web3
from eth_account import Account

w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_KEY"))

# Ваш приватный ключ (НИКОГДА не хардкодьте в реальных приложениях!)
private_key = "0x..."
account = Account.from_key(private_key)

# Получаем текущие gas параметры
latest_block = w3.eth.get_block('latest')
base_fee = latest_block['baseFeePerGas']

# Рекомендуемые значения
max_priority_fee = w3.to_wei(2, 'gwei')  # Чаевые майнерам
max_fee = base_fee * 2 + max_priority_fee  # Максимальная цена за газ

# Создание транзакции
transaction = {
    'type': 2,  # EIP-1559
    'chainId': w3.eth.chain_id,
    'from': account.address,
    'to': '0xRecipientAddress...',
    'value': w3.to_wei(0.01, 'ether'),
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 21000,  # Стандартный газ для простого перевода
    'maxFeePerGas': max_fee,
    'maxPriorityFeePerGas': max_priority_fee,
}

# Подпись транзакции
signed_tx = w3.eth.account.sign_transaction(transaction, private_key)

# Отправка транзакции
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print(f"TX Hash: {tx_hash.hex()}")

# Ожидание подтверждения
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Статус: {'Успешно' if receipt['status'] == 1 else 'Ошибка'}")
print(f"Использовано газа: {receipt['gasUsed']}")
print(f"Номер блока: {receipt['blockNumber']}")
```

### Отправка ETH (Legacy транзакция)

```python
# Legacy транзакция (для сетей без EIP-1559)
transaction = {
    'chainId': w3.eth.chain_id,
    'from': account.address,
    'to': '0xRecipientAddress...',
    'value': w3.to_wei(0.01, 'ether'),
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 21000,
    'gasPrice': w3.eth.gas_price,  # Текущая цена газа
}

signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
```

### Оценка газа

```python
# Оценка необходимого газа
estimated_gas = w3.eth.estimate_gas({
    'from': account.address,
    'to': '0xRecipientAddress...',
    'value': w3.to_wei(0.01, 'ether'),
})
print(f"Необходимо газа: {estimated_gas}")

# Добавляем запас 20%
gas_with_buffer = int(estimated_gas * 1.2)
```

### Получение информации о транзакции

```python
tx_hash = "0x..."

# Получение транзакции
tx = w3.eth.get_transaction(tx_hash)
print(f"От: {tx['from']}")
print(f"К: {tx['to']}")
print(f"Сумма: {w3.from_wei(tx['value'], 'ether')} ETH")
print(f"Gas Price: {w3.from_wei(tx['gasPrice'], 'gwei')} Gwei")
print(f"Nonce: {tx['nonce']}")

# Получение чека транзакции
receipt = w3.eth.get_transaction_receipt(tx_hash)
print(f"Статус: {receipt['status']}")
print(f"Газ использован: {receipt['gasUsed']}")
print(f"Эффективная цена газа: {w3.from_wei(receipt['effectiveGasPrice'], 'gwei')} Gwei")
print(f"Номер блока: {receipt['blockNumber']}")
```

### Ускорение транзакции (Speed Up)

```python
# Если транзакция застряла, можно её ускорить,
# отправив новую с тем же nonce но выше gas price

original_nonce = 42  # nonce застрявшей транзакции
new_gas_price = w3.eth.gas_price * 1.5  # +50% к текущей цене

speed_up_tx = {
    'chainId': w3.eth.chain_id,
    'from': account.address,
    'to': '0xRecipientAddress...',
    'value': w3.to_wei(0.01, 'ether'),
    'nonce': original_nonce,  # Тот же nonce!
    'gas': 21000,
    'gasPrice': int(new_gas_price),
}

signed_tx = w3.eth.account.sign_transaction(speed_up_tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
```

### Отмена транзакции

```python
# Отмена — это отправка 0 ETH себе с тем же nonce

cancel_tx = {
    'chainId': w3.eth.chain_id,
    'from': account.address,
    'to': account.address,  # Отправляем себе
    'value': 0,
    'nonce': original_nonce,  # Тот же nonce!
    'gas': 21000,
    'gasPrice': int(w3.eth.gas_price * 1.5),  # Выше цена
}

signed_tx = w3.eth.account.sign_transaction(cancel_tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
```

### Batch транзакции (множественная отправка)

```python
def send_batch_transactions(w3, private_key, recipients):
    """
    Отправка ETH нескольким получателям
    recipients: list of tuples (address, amount_in_eth)
    """
    account = Account.from_key(private_key)
    nonce = w3.eth.get_transaction_count(account.address)
    
    tx_hashes = []
    
    for to_address, amount_eth in recipients:
        tx = {
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'to': to_address,
            'value': w3.to_wei(amount_eth, 'ether'),
            'nonce': nonce,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
        }
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hashes.append(tx_hash)
        
        nonce += 1  # Увеличиваем nonce для следующей транзакции
        
    return tx_hashes

# Использование
recipients = [
    ("0xAddress1...", 0.01),
    ("0xAddress2...", 0.02),
    ("0xAddress3...", 0.015),
]
hashes = send_batch_transactions(w3, private_key, recipients)
```

---

## Смарт-контракты

### Структура ABI

ABI (Application Binary Interface) — это JSON-описание интерфейса контракта:

```python
# Пример ABI для ERC-20 токена
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_from", "type": "address"},
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transferFrom",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "owner", "type": "address"},
            {"indexed": True, "name": "spender", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Approval",
        "type": "event"
    }
]
```

### Создание объекта контракта

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_KEY"))

# Адрес контракта (USDT на Ethereum Mainnet)
contract_address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

# Создание объекта контракта
contract = w3.eth.contract(address=contract_address, abi=ERC20_ABI)

# Доступ к функциям
print(f"Доступные функции: {contract.functions}")
print(f"Доступные события: {contract.events}")
```

### Чтение данных из контракта (call)

```python
# USDT контракт
usdt_address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
contract = w3.eth.contract(address=usdt_address, abi=ERC20_ABI)

# Вызов view/pure функций (бесплатно, не требует газа)
name = contract.functions.name().call()
symbol = contract.functions.symbol().call()
decimals = contract.functions.decimals().call()
total_supply = contract.functions.totalSupply().call()

print(f"Название: {name}")
print(f"Символ: {symbol}")
print(f"Decimals: {decimals}")
print(f"Total Supply: {total_supply / 10**decimals}")

# Баланс токенов у адреса
holder_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
balance = contract.functions.balanceOf(holder_address).call()
print(f"Баланс {symbol}: {balance / 10**decimals}")

# Проверка allowance
owner = "0xOwnerAddress..."
spender = "0xSpenderAddress..."
allowance = contract.functions.allowance(owner, spender).call()
print(f"Allowance: {allowance / 10**decimals}")
```

### Отправка транзакций в контракт

```python
from eth_account import Account

private_key = "0x..."
account = Account.from_key(private_key)

# Параметры транзакции
to_address = "0xRecipientAddress..."
amount = 100 * 10**6  # 100 USDT (6 decimals)

# Построение транзакции
tx = contract.functions.transfer(
    to_address,
    amount
).build_transaction({
    'chainId': w3.eth.chain_id,
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 100000,  # Оценить с estimate_gas
    'maxFeePerGas': w3.to_wei(50, 'gwei'),
    'maxPriorityFeePerGas': w3.to_wei(2, 'gwei'),
})

# Оценка газа
estimated_gas = w3.eth.estimate_gas(tx)
tx['gas'] = int(estimated_gas * 1.2)

# Подпись и отправка
signed_tx = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

print(f"TX Hash: {tx_hash.hex()}")

# Ожидание подтверждения
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Статус: {'Успешно' if receipt['status'] == 1 else 'Ошибка'}")
```

### Approve и TransferFrom

```python
# Шаг 1: Approve (разрешение на списание)
spender_address = "0xDEXContractAddress..."  # Например, Uniswap Router
amount_to_approve = 2**256 - 1  # Max approval (бесконечно)

approve_tx = contract.functions.approve(
    spender_address,
    amount_to_approve
).build_transaction({
    'chainId': w3.eth.chain_id,
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 60000,
    'maxFeePerGas': w3.to_wei(50, 'gwei'),
    'maxPriorityFeePerGas': w3.to_wei(2, 'gwei'),
})

signed_tx = w3.eth.account.sign_transaction(approve_tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

# Шаг 2: TransferFrom (списание другим контрактом)
# Обычно это делает DEX или другой смарт-контракт
```

### Деплой смарт-контракта

```python
# Компилированный bytecode контракта
contract_bytecode = "0x608060405234801561001057600080fd5b50..."

# ABI контракта
contract_abi = [...]

# Создание объекта для деплоя
Contract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

# Построение транзакции деплоя
# Конструктор может принимать аргументы
constructor_args = ["Token Name", "TKN", 18, 1000000]

deploy_tx = Contract.constructor(*constructor_args).build_transaction({
    'chainId': w3.eth.chain_id,
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 3000000,
    'maxFeePerGas': w3.to_wei(50, 'gwei'),
    'maxPriorityFeePerGas': w3.to_wei(2, 'gwei'),
})

# Подпись и отправка
signed_tx = w3.eth.account.sign_transaction(deploy_tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

# Ожидание деплоя
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
contract_address = receipt['contractAddress']

print(f"Контракт задеплоен: {contract_address}")

# Создание инстанса задеплоенного контракта
deployed_contract = w3.eth.contract(address=contract_address, abi=contract_abi)
```

### Работа с Proxy контрактами

```python
# Для Proxy контрактов нужно использовать ABI имплементации,
# но адрес прокси

proxy_address = "0xProxyAddress..."
implementation_abi = [...]  # ABI имплементации, не прокси

contract = w3.eth.contract(address=proxy_address, abi=implementation_abi)

# Теперь можно вызывать функции имплементации через прокси
result = contract.functions.someFunction().call()
```

### Мультивызовы (Multicall)

```python
# Multicall3 контракт для batch вызовов
MULTICALL3_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"
MULTICALL3_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"name": "target", "type": "address"},
                    {"name": "callData", "type": "bytes"}
                ],
                "name": "calls",
                "type": "tuple[]"
            }
        ],
        "name": "aggregate",
        "outputs": [
            {"name": "blockNumber", "type": "uint256"},
            {"name": "returnData", "type": "bytes[]"}
        ],
        "type": "function"
    }
]

multicall = w3.eth.contract(address=MULTICALL3_ADDRESS, abi=MULTICALL3_ABI)

# Подготовка вызовов
usdt_contract = w3.eth.contract(address=usdt_address, abi=ERC20_ABI)

calls = [
    {
        "target": usdt_address,
        "callData": usdt_contract.encodeABI(fn_name="name")
    },
    {
        "target": usdt_address,
        "callData": usdt_contract.encodeABI(fn_name="symbol")
    },
    {
        "target": usdt_address,
        "callData": usdt_contract.encodeABI(
            fn_name="balanceOf",
            args=["0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"]
        )
    }
]

# Выполнение мультивызова (один RPC запрос вместо трёх)
block_number, return_data = multicall.functions.aggregate(calls).call()

# Декодирование результатов
name = w3.codec.decode(['string'], return_data[0])[0]
symbol = w3.codec.decode(['string'], return_data[1])[0]
balance = w3.codec.decode(['uint256'], return_data[2])[0]

print(f"Name: {name}, Symbol: {symbol}, Balance: {balance}")
```

---

## События и логи

### Получение событий

```python
# Создание фильтра для событий Transfer
transfer_filter = contract.events.Transfer.create_filter(
    from_block='latest'
)

# Получение новых событий
events = transfer_filter.get_new_entries()
for event in events:
    print(f"От: {event['args']['from']}")
    print(f"К: {event['args']['to']}")
    print(f"Сумма: {event['args']['value']}")
    print(f"TX: {event['transactionHash'].hex()}")
    print("---")
```

### Получение исторических событий

```python
# Получение всех Transfer событий за диапазон блоков
events = contract.events.Transfer.get_logs(
    from_block=18000000,
    to_block=18000100
)

for event in events:
    print(f"Блок: {event['blockNumber']}")
    print(f"От: {event['args']['from']}")
    print(f"К: {event['args']['to']}")
    print(f"Сумма: {event['args']['value'] / 10**6}")  # Для USDT
```

### Фильтрация по параметрам

```python
# Только события Transfer ОТ определённого адреса
specific_sender = "0xSenderAddress..."

events = contract.events.Transfer.get_logs(
    from_block=18000000,
    to_block='latest',
    argument_filters={'from': specific_sender}
)

# Только события Transfer К определённому адресу
specific_receiver = "0xReceiverAddress..."

events = contract.events.Transfer.get_logs(
    from_block=18000000,
    to_block='latest',
    argument_filters={'to': specific_receiver}
)

# Фильтр по нескольким адресам
addresses = ["0xAddr1...", "0xAddr2..."]
events = contract.events.Transfer.get_logs(
    from_block=18000000,
    to_block='latest',
    argument_filters={'from': addresses}  # ИЛИ между адресами
)
```

### Работа с сырыми логами

```python
# Получение сырых логов
logs = w3.eth.get_logs({
    'fromBlock': 18000000,
    'toBlock': 18000100,
    'address': usdt_address,
    'topics': [
        # Transfer event signature
        w3.keccak(text="Transfer(address,address,uint256)").hex()
    ]
})

# Декодирование логов
for log in logs:
    # Декодируем с помощью контракта
    decoded = contract.events.Transfer().process_log(log)
    print(decoded)
```

### Подписка на события (WebSocket)

```python
import asyncio
from web3 import AsyncWeb3

async def listen_events():
    w3 = AsyncWeb3(AsyncWeb3.WebSocketProvider(
        "wss://mainnet.infura.io/ws/v3/YOUR_KEY"
    ))
    
    contract = w3.eth.contract(address=usdt_address, abi=ERC20_ABI)
    
    # Создание фильтра
    event_filter = await contract.events.Transfer.create_filter(
        from_block='latest'
    )
    
    while True:
        events = await event_filter.get_new_entries()
        for event in events:
            print(f"Новый Transfer: {event['args']}")
        await asyncio.sleep(2)

# Запуск
asyncio.run(listen_events())
```

### Парсинг событий из транзакции

```python
# Получение всех событий из транзакции
tx_hash = "0x..."
receipt = w3.eth.get_transaction_receipt(tx_hash)

# Парсинг всех Transfer событий
transfer_events = contract.events.Transfer().process_receipt(receipt)

for event in transfer_events:
    print(f"Transfer: {event['args']}")

# Парсинг всех событий всех типов
all_events = contract.events.Transfer().process_receipt(
    receipt, 
    errors=web3.logs.DISCARD  # Игнорировать ошибки декодирования
)
```

---

## Работа с ENS

ENS (Ethereum Name Service) — децентрализованная система доменных имён.

### Настройка ENS

```python
from web3 import Web3
from ens import ENS

w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_KEY"))

# ENS доступен через w3.ens
# или можно создать отдельный объект
ns = ENS.from_web3(w3)
```

### Разрешение имён

```python
# ENS имя -> Адрес
address = w3.ens.address('vitalik.eth')
print(f"vitalik.eth -> {address}")

# Адрес -> ENS имя (Reverse Resolution)
name = w3.ens.name('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045')
print(f"Адрес -> {name}")
```

### Получение записей ENS

```python
from ens import ENS

ns = ENS.from_web3(w3)

# Текстовые записи
avatar = ns.get_text('vitalik.eth', 'avatar')
twitter = ns.get_text('vitalik.eth', 'com.twitter')
github = ns.get_text('vitalik.eth', 'com.github')
url = ns.get_text('vitalik.eth', 'url')
email = ns.get_text('vitalik.eth', 'email')

print(f"Avatar: {avatar}")
print(f"Twitter: {twitter}")
print(f"GitHub: {github}")
print(f"URL: {url}")
print(f"Email: {email}")

# Content Hash (IPFS, Swarm и др.)
content_hash = ns.get_contenthash('vitalik.eth')
print(f"Content Hash: {content_hash}")
```

### Проверка владельца

```python
# Владелец ENS имени
owner = ns.owner('vitalik.eth')
print(f"Владелец: {owner}")
```

### Использование ENS в транзакциях

```python
# Web3.py автоматически разрешает ENS имена
balance = w3.eth.get_balance('vitalik.eth')
print(f"Баланс vitalik.eth: {w3.from_wei(balance, 'ether')} ETH")

# В транзакциях тоже можно использовать ENS
tx = {
    'to': 'vitalik.eth',  # Автоматически разрешится в адрес
    'value': w3.to_wei(0.01, 'ether'),
    # ...
}
```

---

## Утилиты и хелперы

### Конвертация единиц

```python
from web3 import Web3

# Wei -> Ether
wei_amount = 1000000000000000000  # 1 ETH в Wei
eth_amount = Web3.from_wei(wei_amount, 'ether')
print(f"{wei_amount} Wei = {eth_amount} ETH")

# Ether -> Wei
eth_amount = 1.5
wei_amount = Web3.to_wei(eth_amount, 'ether')
print(f"{eth_amount} ETH = {wei_amount} Wei")

# Все доступные единицы
units = ['wei', 'kwei', 'babbage', 'femtoether', 'mwei', 'lovelace', 
         'picoether', 'gwei', 'shannon', 'nanoether', 'nano', 
         'szabo', 'microether', 'micro', 'finney', 'milliether', 
         'milli', 'ether', 'kether', 'grand', 'mether', 'gether', 'tether']

# Примеры
print(Web3.to_wei(1, 'gwei'))      # 1000000000
print(Web3.to_wei(1, 'ether'))     # 1000000000000000000
print(Web3.from_wei(1e18, 'ether')) # 1.0
```

### Хеширование

```python
from web3 import Web3

# Keccak256 (SHA3)
hash_result = Web3.keccak(text="Hello, World!")
print(f"Keccak256: {hash_result.hex()}")

# Хеширование bytes
hash_result = Web3.keccak(b"Hello, World!")
print(f"Keccak256: {hash_result.hex()}")

# Хеширование hex
hash_result = Web3.keccak(hexstr="0x48656c6c6f")
print(f"Keccak256: {hash_result.hex()}")

# Solidity keccak256(abi.encodePacked(...))
from eth_abi.packed import encode_packed

packed = encode_packed(['address', 'uint256'], 
                       ['0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045', 100])
hash_result = Web3.keccak(packed)
```

### Кодирование и декодирование

```python
from web3 import Web3
from eth_abi import encode, decode

# ABI кодирование
encoded = encode(['uint256', 'address'], 
                 [100, '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'])
print(f"Encoded: {encoded.hex()}")

# ABI декодирование
decoded = decode(['uint256', 'address'], encoded)
print(f"Decoded: {decoded}")

# Кодирование вызова функции
contract = w3.eth.contract(address=usdt_address, abi=ERC20_ABI)
call_data = contract.encodeABI(
    fn_name='transfer',
    args=['0xRecipient...', 1000000]
)
print(f"Call data: {call_data}")
```

### Hex утилиты

```python
from web3 import Web3

# String -> Hex
hex_value = Web3.to_hex(text="Hello")
print(f"Text to Hex: {hex_value}")

# Bytes -> Hex
hex_value = Web3.to_hex(b"Hello")
print(f"Bytes to Hex: {hex_value}")

# Int -> Hex
hex_value = Web3.to_hex(255)
print(f"Int to Hex: {hex_value}")

# Hex -> Bytes
bytes_value = Web3.to_bytes(hexstr="0x48656c6c6f")
print(f"Hex to Bytes: {bytes_value}")

# Hex -> Int
int_value = Web3.to_int(hexstr="0xff")
print(f"Hex to Int: {int_value}")

# Hex -> Text
text_value = Web3.to_text(hexstr="0x48656c6c6f")
print(f"Hex to Text: {text_value}")
```

### Подпись и верификация сообщений

```python
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

w3 = Web3()

# Подпись сообщения
private_key = "0x..."
message = "Hello, Ethereum!"

# Создание сообщения в формате EIP-191
message_encoded = encode_defunct(text=message)

# Подпись
signed_message = w3.eth.account.sign_message(message_encoded, private_key)

print(f"Message Hash: {signed_message.messageHash.hex()}")
print(f"Signature: {signed_message.signature.hex()}")
print(f"r: {hex(signed_message.r)}")
print(f"s: {hex(signed_message.s)}")
print(f"v: {signed_message.v}")

# Верификация подписи (восстановление адреса)
recovered_address = w3.eth.account.recover_message(
    message_encoded, 
    signature=signed_message.signature
)
print(f"Recovered Address: {recovered_address}")
```

### EIP-712 Typed Data Signature

```python
from eth_account import Account
from eth_account.messages import encode_typed_data

# Определение структуры данных (EIP-712)
typed_data = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "Permit": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "nonce", "type": "uint256"},
            {"name": "deadline", "type": "uint256"}
        ]
    },
    "primaryType": "Permit",
    "domain": {
        "name": "MyToken",
        "version": "1",
        "chainId": 1,
        "verifyingContract": "0xTokenAddress..."
    },
    "message": {
        "owner": "0xOwner...",
        "spender": "0xSpender...",
        "value": 1000000,
        "nonce": 0,
        "deadline": 1700000000
    }
}

# Подпись typed data
signable_message = encode_typed_data(full_message=typed_data)
signed = Account.sign_message(signable_message, private_key)

print(f"Signature: {signed.signature.hex()}")
```

---

## Middleware

Middleware позволяет модифицировать запросы и ответы.

### Встроенные Middleware

```python
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Для PoA сетей (BSC, Polygon и др.)
w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Теперь можно работать с BSC
print(f"Блок: {w3.eth.block_number}")
```

### Gas Price Strategy

```python
from web3 import Web3
from web3.gas_strategies.time_based import medium_gas_price_strategy

w3 = Web3(Web3.HTTPProvider("..."))

# Установка стратегии
w3.eth.set_gas_price_strategy(medium_gas_price_strategy)

# Теперь можно использовать generate_gas_price
gas_price = w3.eth.generate_gas_price()
print(f"Рекомендуемая цена газа: {w3.from_wei(gas_price, 'gwei')} Gwei")
```

### Кастомный Middleware

```python
from web3 import Web3

def simple_cache_middleware(make_request, w3):
    """Простой кэширующий middleware"""
    cache = {}
    
    def middleware(method, params):
        # Кэшируем только некоторые методы
        if method in ['eth_chainId', 'net_version']:
            cache_key = (method, str(params))
            if cache_key in cache:
                return cache[cache_key]
            
            response = make_request(method, params)
            cache[cache_key] = response
            return response
        
        return make_request(method, params)
    
    return middleware

# Применение middleware
w3 = Web3(Web3.HTTPProvider("..."))
w3.middleware_onion.add(simple_cache_middleware)
```

### Логирующий Middleware

```python
import logging

logging.basicConfig(level=logging.DEBUG)

def logging_middleware(make_request, w3):
    """Middleware для логирования всех запросов"""
    def middleware(method, params):
        logging.debug(f"Request: {method} {params}")
        response = make_request(method, params)
        logging.debug(f"Response: {response}")
        return response
    return middleware

w3.middleware_onion.add(logging_middleware)
```

---

## Асинхронная работа

### Асинхронное подключение

```python
import asyncio
from web3 import AsyncWeb3, AsyncHTTPProvider

async def main():
    # Асинхронное подключение
    w3 = AsyncWeb3(AsyncHTTPProvider("https://mainnet.infura.io/v3/YOUR_KEY"))
    
    # Проверка подключения
    connected = await w3.is_connected()
    print(f"Подключено: {connected}")
    
    # Асинхронные запросы
    block_number = await w3.eth.block_number
    print(f"Блок: {block_number}")
    
    # Параллельные запросы
    tasks = [
        w3.eth.get_balance("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"),
        w3.eth.get_transaction_count("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"),
        w3.eth.get_block('latest'),
    ]
    
    results = await asyncio.gather(*tasks)
    balance, nonce, block = results
    
    print(f"Баланс: {w3.from_wei(balance, 'ether')} ETH")
    print(f"Nonce: {nonce}")
    print(f"Последний блок: {block['number']}")

asyncio.run(main())
```

### Асинхронная работа с контрактами

```python
import asyncio
from web3 import AsyncWeb3, AsyncHTTPProvider

async def get_token_info(w3, contract_address, abi):
    contract = w3.eth.contract(address=contract_address, abi=abi)
    
    # Параллельное получение данных
    name, symbol, decimals, total_supply = await asyncio.gather(
        contract.functions.name().call(),
        contract.functions.symbol().call(),
        contract.functions.decimals().call(),
        contract.functions.totalSupply().call(),
    )
    
    return {
        'name': name,
        'symbol': symbol,
        'decimals': decimals,
        'total_supply': total_supply
    }

async def main():
    w3 = AsyncWeb3(AsyncHTTPProvider("https://mainnet.infura.io/v3/YOUR_KEY"))
    
    # Получение информации о нескольких токенах параллельно
    tokens = [
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        "0x6B175474E89094C44Da98b954EescdeCB5e22B",  # DAI
    ]
    
    tasks = [get_token_info(w3, addr, ERC20_ABI) for addr in tokens]
    results = await asyncio.gather(*tasks)
    
    for info in results:
        print(info)

asyncio.run(main())
```

### Асинхронные подписки

```python
import asyncio
from web3 import AsyncWeb3

async def subscribe_to_blocks():
    w3 = AsyncWeb3(AsyncWeb3.WebSocketProvider(
        "wss://mainnet.infura.io/ws/v3/YOUR_KEY"
    ))
    
    # Подписка на новые блоки
    subscription_id = await w3.eth.subscribe('newHeads')
    print(f"Подписка создана: {subscription_id}")
    
    async for response in w3.socket.process_subscriptions():
        block = response['result']
        print(f"Новый блок: {block['number']}")
        print(f"Hash: {block['hash'].hex()}")
        print(f"Транзакций: {len(block.get('transactions', []))}")
        print("---")

asyncio.run(subscribe_to_blocks())
```

---

## Практические примеры

### 1. Мониторинг баланса кошелька

```python
import time
from web3 import Web3

def monitor_balance(w3, address, interval=60):
    """Мониторинг баланса с уведомлениями об изменениях"""
    last_balance = None
    
    while True:
        try:
            current_balance = w3.eth.get_balance(address)
            current_eth = w3.from_wei(current_balance, 'ether')
            
            if last_balance is not None:
                diff = current_balance - last_balance
                if diff != 0:
                    diff_eth = w3.from_wei(abs(diff), 'ether')
                    direction = "+" if diff > 0 else "-"
                    print(f"[{time.strftime('%H:%M:%S')}] "
                          f"Баланс изменился: {direction}{diff_eth} ETH")
                    print(f"Текущий баланс: {current_eth} ETH")
            
            last_balance = current_balance
            
        except Exception as e:
            print(f"Ошибка: {e}")
        
        time.sleep(interval)

# Использование
w3 = Web3(Web3.HTTPProvider("..."))
monitor_balance(w3, "0xYourAddress...", interval=30)
```

### 2. Отслеживание транзакций токена

```python
from web3 import Web3
import time

def track_token_transfers(w3, token_address, token_abi, from_block='latest'):
    """Отслеживание всех Transfer событий токена"""
    contract = w3.eth.contract(address=token_address, abi=token_abi)
    decimals = contract.functions.decimals().call()
    symbol = contract.functions.symbol().call()
    
    event_filter = contract.events.Transfer.create_filter(from_block=from_block)
    
    print(f"Отслеживание переводов {symbol}...")
    
    while True:
        try:
            events = event_filter.get_new_entries()
            
            for event in events:
                amount = event['args']['value'] / 10**decimals
                print(f"\n[Transfer {symbol}]")
                print(f"От: {event['args']['from']}")
                print(f"К: {event['args']['to']}")
                print(f"Сумма: {amount:,.2f} {symbol}")
                print(f"TX: {event['transactionHash'].hex()}")
                
        except Exception as e:
            print(f"Ошибка: {e}")
        
        time.sleep(2)
```

### 3. Проверка баланса ERC-20 токенов

```python
def get_token_balances(w3, wallet_address, token_addresses, token_abi):
    """Получение балансов нескольких токенов"""
    balances = {}
    
    for token_address in token_addresses:
        try:
            contract = w3.eth.contract(address=token_address, abi=token_abi)
            
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            balance = contract.functions.balanceOf(wallet_address).call()
            
            balance_formatted = balance / 10**decimals
            
            balances[symbol] = {
                'name': name,
                'address': token_address,
                'balance': balance_formatted,
                'decimals': decimals
            }
            
        except Exception as e:
            print(f"Ошибка для {token_address}: {e}")
    
    return balances

# Использование
tokens = [
    "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
    "0x6B175474E89094C44Da98b954EedscdeCB5e22B",  # DAI
]

balances = get_token_balances(w3, "0xYourWallet...", tokens, ERC20_ABI)
for symbol, data in balances.items():
    print(f"{symbol}: {data['balance']:,.2f}")
```

### 4. Простой DEX Swap (Uniswap V2 пример)

```python
from web3 import Web3
from eth_account import Account
import time

# Uniswap V2 Router
UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

UNISWAP_V2_ROUTER_ABI = [
    {
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "type": "function"
    },
    {
        "inputs": [
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactETHForTokens",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "payable": True,
        "type": "function"
    },
    {
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "type": "function"
    }
]

def swap_eth_for_tokens(w3, private_key, token_address, eth_amount, slippage=0.5):
    """Обмен ETH на токены через Uniswap V2"""
    account = Account.from_key(private_key)
    router = w3.eth.contract(address=UNISWAP_V2_ROUTER, abi=UNISWAP_V2_ROUTER_ABI)
    
    # Путь обмена: WETH -> Token
    path = [WETH, token_address]
    
    # Получение ожидаемого количества токенов
    amount_in = w3.to_wei(eth_amount, 'ether')
    amounts_out = router.functions.getAmountsOut(amount_in, path).call()
    expected_out = amounts_out[1]
    
    # Минимальное количество с учётом slippage
    min_out = int(expected_out * (1 - slippage / 100))
    
    # Deadline (текущее время + 10 минут)
    deadline = int(time.time()) + 600
    
    # Построение транзакции
    tx = router.functions.swapExactETHForTokens(
        min_out,
        path,
        account.address,
        deadline
    ).build_transaction({
        'chainId': w3.eth.chain_id,
        'from': account.address,
        'value': amount_in,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 250000,
        'maxFeePerGas': w3.to_wei(50, 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei(2, 'gwei'),
    })
    
    # Подпись и отправка
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"Swap TX: {tx_hash.hex()}")
    
    # Ожидание подтверждения
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return receipt
```

### 5. Flashbots (защита от MEV)

```python
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount
import requests

def send_flashbots_bundle(w3, private_key, transactions):
    """Отправка bundle через Flashbots"""
    account = Account.from_key(private_key)
    
    # Подпись транзакций
    signed_txs = []
    for tx in transactions:
        signed = w3.eth.account.sign_transaction(tx, private_key)
        signed_txs.append(signed.rawTransaction.hex())
    
    # Текущий блок
    block_number = w3.eth.block_number
    
    # Параметры bundle
    bundle = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_sendBundle",
        "params": [
            {
                "txs": signed_txs,
                "blockNumber": hex(block_number + 1),
            }
        ]
    }
    
    # Подпись заголовка
    message = Web3.keccak(text=str(bundle))
    signature = account.sign_message(message)
    
    # Отправка в Flashbots
    headers = {
        "X-Flashbots-Signature": f"{account.address}:{signature.signature.hex()}"
    }
    
    response = requests.post(
        "https://relay.flashbots.net",
        json=bundle,
        headers=headers
    )
    
    return response.json()
```

### 6. Gas Tracker

```python
from web3 import Web3
import statistics

def analyze_gas_prices(w3, num_blocks=20):
    """Анализ цен на газ за последние N блоков"""
    latest = w3.eth.block_number
    
    base_fees = []
    priority_fees = []
    
    for block_num in range(latest - num_blocks, latest + 1):
        block = w3.eth.get_block(block_num, full_transactions=True)
        
        if 'baseFeePerGas' in block:
            base_fees.append(block['baseFeePerGas'])
        
        # Анализ priority fees из транзакций
        for tx in block.transactions:
            if 'maxPriorityFeePerGas' in tx:
                priority_fees.append(tx['maxPriorityFeePerGas'])
    
    # Статистика
    result = {
        'base_fee': {
            'current': w3.from_wei(base_fees[-1], 'gwei') if base_fees else 0,
            'avg': w3.from_wei(statistics.mean(base_fees), 'gwei') if base_fees else 0,
            'min': w3.from_wei(min(base_fees), 'gwei') if base_fees else 0,
            'max': w3.from_wei(max(base_fees), 'gwei') if base_fees else 0,
        },
        'priority_fee': {
            'avg': w3.from_wei(statistics.mean(priority_fees), 'gwei') if priority_fees else 0,
            'median': w3.from_wei(statistics.median(priority_fees), 'gwei') if priority_fees else 0,
        },
        'recommendations': {
            'low': w3.from_wei(base_fees[-1] + int(statistics.mean(priority_fees) * 0.8), 'gwei') if priority_fees else 0,
            'medium': w3.from_wei(base_fees[-1] + int(statistics.mean(priority_fees)), 'gwei') if priority_fees else 0,
            'high': w3.from_wei(base_fees[-1] + int(statistics.mean(priority_fees) * 1.5), 'gwei') if priority_fees else 0,
        }
    }
    
    return result

# Использование
gas_info = analyze_gas_prices(w3)
print(f"Base Fee: {gas_info['base_fee']['current']:.2f} Gwei")
print(f"Рекомендации:")
print(f"  Low: {gas_info['recommendations']['low']:.2f} Gwei")
print(f"  Medium: {gas_info['recommendations']['medium']:.2f} Gwei")
print(f"  High: {gas_info['recommendations']['high']:.2f} Gwei")
```

---

## Безопасность

### Правила работы с приватными ключами

```python
import os
from dotenv import load_dotenv

# ❌ НИКОГДА так не делайте!
private_key = "0x4c0883a69102937d623..."

# ✅ Используйте переменные окружения
load_dotenv()
private_key = os.getenv("PRIVATE_KEY")

# ✅ Или keystore файлы с паролем
from eth_account import Account
import getpass

password = getpass.getpass("Введите пароль от keystore: ")
with open("keystore.json", "r") as f:
    keystore = f.read()
private_key = Account.decrypt(keystore, password)
```

### Защита от Replay атак

```python
# Всегда указывайте chainId в транзакциях
tx = {
    'chainId': w3.eth.chain_id,  # Важно!
    'nonce': w3.eth.get_transaction_count(address),
    # ...
}
```

### Проверка адресов

```python
def validate_address(address):
    """Валидация и нормализация адреса"""
    if not Web3.is_address(address):
        raise ValueError(f"Невалидный адрес: {address}")
    
    # Приведение к checksum формату
    return Web3.to_checksum_address(address)

# Использование
try:
    safe_address = validate_address(user_input)
except ValueError as e:
    print(f"Ошибка: {e}")
```

### Проверка контрактов

```python
def is_contract(w3, address):
    """Проверка, является ли адрес контрактом"""
    code = w3.eth.get_code(address)
    return len(code) > 0

# Проверка перед отправкой
if is_contract(w3, recipient):
    print("Внимание: вы отправляете на контракт!")
    # Убедитесь, что контракт может принять ETH
```

### Защита от переполнения

```python
# Проверка на overflow при работе с большими числами
def safe_multiply(a, b, max_value=2**256 - 1):
    result = a * b
    if result > max_value:
        raise ValueError("Overflow detected")
    return result
```

---

## Отладка и решение проблем

### Частые ошибки

#### Ошибка подключения

```python
from web3.exceptions import CannotHandleRequest, ConnectionClosedOK

try:
    block = w3.eth.block_number
except CannotHandleRequest:
    print("Провайдер не может обработать запрос")
except ConnectionClosedOK:
    print("Соединение закрыто")
except Exception as e:
    print(f"Ошибка подключения: {e}")
```

#### Недостаточно газа

```python
from web3.exceptions import ContractLogicError

try:
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt['status'] == 0:
        print("Транзакция откатилась (revert)")
except ContractLogicError as e:
    print(f"Ошибка контракта: {e}")
```

#### Nonce уже использован

```python
# Ошибка: "nonce too low"
# Решение: получить актуальный nonce
nonce = w3.eth.get_transaction_count(address, 'pending')
```

### Логирование

```python
import logging

# Включение логирования web3
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('web3')
logger.setLevel(logging.DEBUG)
```

### Трассировка транзакций

```python
def trace_transaction(w3, tx_hash):
    """Трассировка транзакции (требует archive ноду)"""
    try:
        # Для Geth
        trace = w3.manager.request_blocking(
            'debug_traceTransaction',
            [tx_hash, {}]
        )
        return trace
    except Exception as e:
        print(f"Трассировка недоступна: {e}")
        return None
```

### Отладка контрактов

```python
def decode_revert_reason(w3, tx_hash):
    """Декодирование причины revert"""
    tx = w3.eth.get_transaction(tx_hash)
    
    try:
        # Пытаемся выполнить call
        w3.eth.call({
            'to': tx['to'],
            'from': tx['from'],
            'data': tx['input'],
            'value': tx['value'],
        }, tx['blockNumber'] - 1)
    except Exception as e:
        # Извлекаем revert reason
        error_message = str(e)
        
        # Попробуем декодировать
        if 'revert' in error_message.lower():
            # Ищем hex-кодированное сообщение
            import re
            hex_match = re.search(r'0x[0-9a-fA-F]+', error_message)
            if hex_match:
                try:
                    reason = bytes.fromhex(hex_match.group()[2:]).decode('utf-8')
                    return reason
                except:
                    pass
        
        return error_message
    
    return "Транзакция успешна"
```

---

## Полезные ссылки

- [Официальная документация Web3.py](https://web3py.readthedocs.io/)
- [Ethereum JSON-RPC API](https://ethereum.org/en/developers/docs/apis/json-rpc/)
- [EIP-1559 (Fee Market)](https://eips.ethereum.org/EIPS/eip-1559)
- [EIP-712 (Typed Signatures)](https://eips.ethereum.org/EIPS/eip-712)
- [ERC-20 Стандарт](https://eips.ethereum.org/EIPS/eip-20)
- [Etherscan API](https://docs.etherscan.io/)
- [Infura](https://infura.io/)
- [Alchemy](https://www.alchemy.com/)

---

## Заключение

Web3.py — мощная библиотека для работы с Ethereum. Основные возможности:

1. **Подключение** к нодам через HTTP, WebSocket или IPC
2. **Управление аккаунтами** — создание, импорт, подпись
3. **Транзакции** — отправка ETH и вызов контрактов
4. **Смарт-контракты** — чтение, запись, деплой
5. **События** — мониторинг и подписки
6. **ENS** — работа с доменными именами
7. **Утилиты** — хеширование, конвертация, подпись

Всегда помните о безопасности:
- Храните приватные ключи в переменных окружения
- Используйте checksum адреса
- Проверяйте транзакции перед отправкой
- Тестируйте на тестовых сетях (Sepolia, Goerli)

---

*Документация актуальна для Web3.py версии 6.x*