from brownie import CowContract, Contract, accounts, interface, config,chain
import requests
import web3 

def main():

    dev = accounts.from_mnemonic(config["wallets"]["from_mnemonic"])
    # dev = accounts[0]
    cowContract = CowContract.deploy({'from':dev}) 
    # cowContract = CowContract.deploy({'from':dev}, publish_source = True)
    print("Deploy complete, contract deployed at: {}".format(cowContract.address))

    module_address = cowContract.address

    # usdc = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    sell_token_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    # weth = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    buy_token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

    amount = 1700000000

    if (chain.id == 1):
        # Contract that will receive the order
        gnosis_settlement = Contract.from_explorer("0x9008D19f58AAbD9eD0D60971565AA8510560ab41")
        # Contract we need to approve so our tokens can be transferFrom
        gnosis_vault_relayer = Contract.from_explorer("0xC92E8bdf79f0507f65a392b0ab4667716BFE0110")
        token = Contract.from_explorer(sell_token_address)
    elif (chain.id == 4):
        gnosis_settlement = Contract.from_explorer("0x9008D19f58AAbD9eD0D60971565AA8510560ab41")
        gnosis_vault_relayer = Contract.from_explorer("0xC92E8bdf79f0507f65a392b0ab4667716BFE0110")
        # usdc = Contract.from_explorer("0xeb8f08a975Ab53E34D8a0330E0D34de942C95926")
        token = Contract.from_explorer(sell_token_address)

    # Get some usdc from Circle
    # Only in tests, if you need usdc
    # if (chain.id == 1):
    #     circle = accounts.at("0x55fe002aeff02f77364de339a1292923a15844b8", force =True)
    #     usdc_sender = circle
    #     usdc.transfer(module_address, 10000000000, {'from': usdc_sender})
    # elif (chain.id == 4):
    #     circle = accounts.at("0xc0f97cc918c9d6fa4e9fc6be61a6a06589d199b2", force =True)
    #     usdc_sender = circle
    #     usdc.transfer(module_address, 10000000000, {'from': usdc_sender})
    
    # Approve so we can create a cowswap order  
    token.approve(gnosis_vault_relayer, 2**256-1,{"from": module_address})

    # get the fee + the buy amount after fee
    fee_and_quote = "https://api.cow.fi/mainnet/api/v1/feeAndQuote/sell"
    get_params = {
        "sellToken": sell_token_address,
        "buyToken": buy_token_address,
        "sellAmountBeforeFee": amount
    }
    r = requests.get(fee_and_quote, params=get_params)
    assert r.ok and r.status_code == 200

    # These two values are needed to create an order
    fee_amount = int(r.json()['fee']['amount'])
    buy_amount_after_fee = int(r.json()['buyAmountAfterFee'])
    assert fee_amount > 0
    assert buy_amount_after_fee > 0

    print("Order after fee will buy {}".format(buy_amount_after_fee))

    # Pretty random order deadline :shrug:
    deadline = chain.time() + 60*60*24*100 # 100 days

    # Submit order
    order_payload = {
        "sellToken": sell_token_address,
        "buyToken": buy_token_address,
        "sellAmount": str(amount-fee_amount), # amount that we have minus the fee we have to pay
        "buyAmount": str(buy_amount_after_fee), # buy amount fetched from the previous call
        "validTo": deadline,
        "appData": web3.Web3.keccak(text="Sorry for testing on mainnet").hex(), 
        "feeAmount": str(fee_amount),
        "kind": "sell",
        "partiallyFillable": False,
        "receiver": module_address,
        "signature": "0x",
        "from": module_address,
        "sellTokenBalance": "erc20",
        "buyTokenBalance": "erc20",
        "signingScheme": "presign" # Very important. this tells the api you are going to sign on chain
    }
    orders_url = f"https://protocol-mainnet.gnosis.io/api/v1/orders"
    r = requests.post(orders_url, json=order_payload)
    assert r.ok and r.status_code == 201
    order_uid = r.json()
    print(f"Payload: {order_payload}")
    print(f"Order uid: {order_uid}")

    # With the order id, we set the flag, basically signing as the contract.
    cowContract.sendSetSignatureTx(order_uid, True,{'from': dev})

    # order can be seen here: https://api.cow.fi/docs/#/default/get_api_v1_orders__UID_

    # https://docs.cow.fi/tutorials/cowswap-trades-with-a-gnosis-safe-wallet
    # Alternatives:
    # https://docs.1inch.io/docs/limit-order-protocol/guide/create-limit-order/
    # https://docs.0x.org/0x-api-swap/guides/use-0x-api-liquidity-in-your-smart-contracts


