// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

interface INexorCredit {
    // 0 = NONE, 1 = D, 2 = C, 3 = B, 4 = A
    function creditBandOf(address account) external view returns (uint8);
}

contract NexorLend is Ownable {
    struct Loan {
        address borrower;
        uint256 principal;
        uint256 collateral;
        bool repaid;
        bool liquidated;
    }

    INexorCredit public immutable credit;
    address public vault;

    uint256 public nextLoanId = 1;
    mapping(uint256 => Loan) private _loans;

    event Borrowed(uint256 indexed loanId, address indexed borrower, uint256 amount, uint256 collateral, uint8 band, uint256 ratio);
    event Repaid(uint256 indexed loanId, address indexed payer, uint256 amount);
    event AutoRepaid(uint256 indexed loanId, address indexed caller, uint256 amount);
    event Liquidated(uint256 indexed loanId, address indexed caller);
    event VaultUpdated(address indexed newVault);

    constructor(address creditContract, address vault_) Ownable(msg.sender) {
        require(creditContract != address(0), "NexorLend: credit required");
        require(vault_ != address(0), "NexorLend: vault required");
        credit = INexorCredit(creditContract);
        vault = vault_;
    }

    modifier onlyVault() {
        require(msg.sender == vault || msg.sender == owner(), "NexorLend: only vault or owner");
        _;
    }

    function setVault(address newVault) external onlyOwner {
        require(newVault != address(0), "NexorLend: vault required");
        vault = newVault;
        emit VaultUpdated(newVault);
    }

    function borrow(uint256 amount, uint256 collateral) external returns (uint256 loanId) {
        require(amount > 0, "NexorLend: amount zero");

        uint8 band = credit.creditBandOf(msg.sender);
        require(band >= 1 && band <= 4, "NexorLend: invalid band");

        uint256 ratio = _ratioForBand(band);
        require(collateral >= (amount * ratio) / 100, "NexorLend: insufficient collateral");

        loanId = nextLoanId++;
        _loans[loanId] = Loan({
            borrower: msg.sender,
            principal: amount,
            collateral: collateral,
            repaid: false,
            liquidated: false
        });

        emit Borrowed(loanId, msg.sender, amount, collateral, band, ratio);
    }

    function repay(uint256 loanId, uint256 amount) external {
        Loan storage loan = _loans[loanId];
        require(loan.borrower != address(0), "NexorLend: invalid loan");
        require(!loan.repaid && !loan.liquidated, "NexorLend: closed");
        require(msg.sender == loan.borrower, "NexorLend: not borrower");
        require(amount >= loan.principal, "NexorLend: amount too low");

        loan.repaid = true;
        emit Repaid(loanId, msg.sender, amount);
    }

    function autoRepay(uint256 loanId, uint256 amount) external onlyVault {
        Loan storage loan = _loans[loanId];
        require(loan.borrower != address(0), "NexorLend: invalid loan");
        require(!loan.repaid && !loan.liquidated, "NexorLend: closed");
        require(amount >= loan.principal, "NexorLend: amount too low");

        loan.repaid = true;
        emit AutoRepaid(loanId, msg.sender, amount);
    }

    function liquidate(uint256 loanId, uint256 currentCollateralValue) external {
        Loan storage loan = _loans[loanId];
        require(loan.borrower != address(0), "NexorLend: invalid loan");
        require(!loan.repaid && !loan.liquidated, "NexorLend: closed");

        uint8 band = credit.creditBandOf(loan.borrower);
        require(band >= 1 && band <= 4, "NexorLend: invalid band");

        uint256 requiredCollateral = (loan.principal * _ratioForBand(band)) / 100;
        uint256 healthFactor = (currentCollateralValue * 1e18) / requiredCollateral;
        require(healthFactor < 1e18, "NexorLend: healthy");

        loan.liquidated = true;
        emit Liquidated(loanId, msg.sender);
    }

    function getLoan(uint256 loanId) external view returns (Loan memory) {
        return _loans[loanId];
    }

    function _ratioForBand(uint8 band) internal pure returns (uint256) {
        if (band == 4) return 120; // A
        if (band == 3) return 130; // B
        if (band == 2) return 140; // C
        if (band == 1) return 150; // D
        revert("NexorLend: invalid band");
    }
}

