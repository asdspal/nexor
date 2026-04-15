// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/// @title NexorVault (Blueprint Section 5.4)
/// @notice Holds protocol funds, executes backend-provided strategies, and sweeps / withdraws yield
/// @dev ERC-4337 compatible in that execution can be delegated to an authorized vault operator
contract NexorVault is Ownable, ReentrancyGuard {
    struct Call {
        address to;
        uint256 value;
        bytes data;
    }

    /// @notice Authorized operator (backend / ERC-4337 wallet) allowed to run strategies and sweep yield
    address public vaultOperator;

    /// @notice Running accounting of recognized yield (denominated in native token held by the vault)
    uint256 public accumulatedYield;

    event VaultOperatorUpdated(address indexed newOperator);
    event StrategyCallExecuted(address indexed to, uint256 value, bytes data, bytes returnData);
    event YieldAccumulated(uint256 amount, uint256 newTotal);
    event YieldWithdrawn(address indexed user, uint256 amount);

    error OnlyVault();
    error StrategyCallFailed();
    error ZeroAddress();
    error ZeroAmount();
    error InsufficientYield();
    error TransferFailed();

    modifier onlyVault() {
        if (msg.sender != vaultOperator && msg.sender != owner()) {
            revert OnlyVault();
        }
        _;
    }

    constructor(address operator_) Ownable(msg.sender) {
        if (operator_ == address(0)) revert ZeroAddress();
        vaultOperator = operator_;
        emit VaultOperatorUpdated(operator_);
    }

    /// @notice Update the authorized vault operator (e.g., ERC-4337 smart account / backend executor)
    function setVaultOperator(address newOperator) external onlyOwner {
        if (newOperator == address(0)) revert ZeroAddress();
        vaultOperator = newOperator;
        emit VaultOperatorUpdated(newOperator);
    }

    /// @notice Execute a batch of low-level calls as part of a strategy
    /// @dev Each element is abi.encode(Call({to, value, data})). Reverts bubbling the original reason.
    function executeStrategy(bytes[] calldata calls) external onlyVault nonReentrant {
        for (uint256 i = 0; i < calls.length; i++) {
            Call memory decoded = abi.decode(calls[i], (Call));
            (bool ok, bytes memory ret) = decoded.to.call{value: decoded.value}(decoded.data);
            if (!ok) {
                _revertWithReason(ret);
                revert StrategyCallFailed(); // unreachable, but keeps compiler satisfied
            }
            emit StrategyCallExecuted(decoded.to, decoded.value, decoded.data, ret);
        }
    }

    /// @notice Sweep any newly accrued native token balance into accounted yield
    /// @dev Intended to be triggered by backend cron; does not move funds, only accounts for them
    function accumulateYield() external onlyVault returns (uint256 newlyAccrued) {
        uint256 currentBalance = address(this).balance;
        if (currentBalance > accumulatedYield) {
            newlyAccrued = currentBalance - accumulatedYield;
            accumulatedYield = currentBalance;
            emit YieldAccumulated(newlyAccrued, accumulatedYield);
        }
    }

    /// @notice Withdraw accounted yield to a user (custodial payout)
    function withdrawYield(address payable user, uint256 amount) external onlyOwner nonReentrant {
        if (user == address(0)) revert ZeroAddress();
        if (amount == 0) revert ZeroAmount();
        if (amount > accumulatedYield) revert InsufficientYield();

        accumulatedYield -= amount;
        (bool ok, ) = user.call{value: amount}("");
        if (!ok) revert TransferFailed();

        emit YieldWithdrawn(user, amount);
    }

    /// @dev Bubble up low-level call reverts with original data
    function _revertWithReason(bytes memory ret) private pure {
        if (ret.length > 0) {
            assembly {
                revert(add(ret, 32), mload(ret))
            }
        }
        revert StrategyCallFailed();
    }

    /// @notice Accept native token transfers (e.g., strategy proceeds)
    receive() external payable {}
}
