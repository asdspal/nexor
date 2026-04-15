"""ZK proof verification and on-chain mint orchestration.

Blueprint Section 3.1 / 7.2 bindings:
- Verify Groth16 proof via snarkjs (Node subprocess) using verification_key.json
- If valid: call NexorCredit.sol mintCreditBand (stubbed Web3 interaction placeholder)
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class VerificationError(Exception):
    """Raised when proof verification fails."""


SNARKJS_CMD = ["node", "npx", "snarkjs"]  # allow override if needed


def verify_proof_with_snarkjs(
    verification_key_path: Path, proof: dict[str, Any], public_signals: list[Any]
) -> bool:
    """Invoke snarkjs groth16 verify via subprocess.

    Args:
        verification_key_path: Path to verification_key.json
        proof: Proof object from frontend (JSON-compatible)
        public_signals: Public signals array
    Returns:
        bool indicating verification success
    Raises:
        VerificationError on execution errors
    """

    input_payload = {
        "vk": json.loads(verification_key_path.read_text()),
        "proof": proof,
        "publicSignals": public_signals,
    }

    try:
        proc = subprocess.run(
            ["node", "-e", "const fs=require('fs'); const snarkjs=require('snarkjs'); const input=JSON.parse(fs.readFileSync(0,'utf8')); (async()=>{const ok=await snarkjs.groth16.verify(input.vk, input.publicSignals, input.proof); console.log(ok? 'true':'false');})();"],
            input=json.dumps(input_payload),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:  # node or snarkjs missing
        raise VerificationError("snarkjs not available; ensure Node + snarkjs installed") from exc

    if proc.returncode != 0:
        raise VerificationError(f"snarkjs verify failed: {proc.stderr.strip()}")

    return proc.stdout.strip().lower() == "true"


def mint_credit_band_stub(wallet_address: str, band: str) -> str:
    """Placeholder for on-chain call.

    Returns a pseudo tx hash string; replace with Web3.py/Ape implementation.
    """

    # TODO: integrate Web3.py with HashKey RPC + NexorCredit ABI
    return f"stub-tx-{wallet_address}-{band}"

