# Nexor

Nexor is a modular zk-credit and on-chain lending platform composed of four workspaces:

- [nexor-backend/](nexor-backend/): FastAPI service for auth, strategies, loans, and credit proofs.
- [nexor-frontend/](nexor-frontend/): Next.js client for dashboards, strategies, loans, and credit proof flows.
- [nexor-contracts/](nexor-contracts/): Hardhat workspace for core smart contracts (credit, lend, vault) and integration tests.
- [nexor-circuits/](nexor-circuits/): Circom circuits and proving assets for credit scoring.


## Prerequisites
- Node.js 18+
- Python 3.12+
- npm (frontend, contracts) and pip (backend)

## Backend (FastAPI)
1. Setup
```bash
cd nexor-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2. Environment
- Create `.env` (see `app/core/config.py` for expected keys). Keep secrets out of git.
3. Run API
```bash
uvicorn app.main:app --reload
```

## Frontend (Next.js)
1. Install
```bash
cd nexor-frontend
npm install
```
2. Environment
- Copy `.env.example` to `.env.local` (if present) and fill required values.
3. Dev server
```bash
npm run dev
```

## Contracts (Hardhat)
1. Install
```bash
cd nexor-contracts
npm install
```
2. Test
```bash
npx hardhat test
```

## Circuits
- Prebuilt artifacts live in [nexor-circuits/build/](nexor-circuits/build/).
- To regenerate, install circom/snarkjs and recompile using project scripts (not included here).

## Repo hygiene
- Secrets: `.env`, `.env.local`, and any `.env*` files are ignored.
- Virtualenvs: `.venv` folders are ignored; recreate locally as needed.
- Embedded repos: `nexor-circuits/circomlib` and `nexor-frontend` were previously embedded; treat them as part of this repo or convert to submodules if desired.
