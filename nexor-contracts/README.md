# Nexor Contracts

## Deployment (HashKey Chain Testnet)

### Prerequisites
1. Install dependencies
```bash
cd nexor-contracts
npm install
```
2. Configure environment
Copy `.env.example` to `.env` and fill:
```
HASHKEY_RPC_URL=https://rpc-testnet.hashkeychain.com
PRIVATE_KEY=0x...
HASHKEY_EXPLORER_API_KEY=your-key
HASHKEY_EXPLORER_API_URL=https://explorer-api-testnet.hashkeychain.com/api
HASHKEY_EXPLORER_BROWSER_URL=https://explorer-testnet.hashkeychain.com
NEXOR_VAULT_ADDRESS=0x... (vault or placeholder)
```

### Deploy
```bash
npx hardhat run scripts/deploy.js --network hashkey_testnet
```
Expected JSON output includes addresses for `Groth16Verifier`, `NexorCredit`, and `NexorLend`.

### Verify
Run for each address with constructor args:
```bash
# Groth16Verifier (no args)
npx hardhat verify --network hashkey_testnet <VERIFIER_ADDRESS>

# NexorCredit(verifier)
npx hardhat verify --network hashkey_testnet <CREDIT_ADDRESS> <VERIFIER_ADDRESS>

# NexorLend(credit, vault)
npx hardhat verify --network hashkey_testnet <LEND_ADDRESS> <CREDIT_ADDRESS> <VAULT_ADDRESS>
```

### Record deployments
Update `deployments.json` with the returned addresses and vault used.

### Explorer manual checks
1. Open `<browserURL>/address/<ADDRESS>#code` → ensure **Verified** status.
2. For `NexorCredit`, check **Read Contract** → `creditBandOf` for a test address.

### Git hygiene
After successful deploy + verify:
```bash
git add .
git commit -m "chore(contracts): deploy to hashkey testnet"
```
