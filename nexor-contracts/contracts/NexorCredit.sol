// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";

interface IGroth16Verifier {
    function verifyProof(
        uint[2] calldata _pA,
        uint[2][2] calldata _pB,
        uint[2] calldata _pC,
        uint[2] calldata _pubSignals
    ) external view returns (bool);
}

interface IERC5192 {
    event Locked(uint256 tokenId);
    event Unlocked(uint256 tokenId);

    function locked(uint256 tokenId) external view returns (bool);
}

abstract contract ERC5192 is ERC721, IERC5192 {
    function locked(uint256 tokenId) public view virtual override returns (bool) {
        require(_ownerOf(tokenId) != address(0), "ERC5192: invalid tokenId");
        return true;
    }

    function _update(address to, uint256 tokenId, address auth) internal virtual override returns (address) {
        address from = _ownerOf(tokenId);
        if (from != address(0) && to != address(0)) {
            revert("ERC5192: transfers are locked");
        }
        return super._update(to, tokenId, auth);
    }

    function approve(address, uint256) public virtual override {
        revert("ERC5192: approvals disabled");
    }

    function setApprovalForAll(address, bool) public virtual override {
        revert("ERC5192: approvals disabled");
    }
}

contract NexorCredit is ERC5192 {
    IGroth16Verifier public immutable verifier;

    // 0 = NONE, 1 = D, 2 = C, 3 = B, 4 = A
    mapping(address => uint8) private _creditBand;

    event CreditBandMinted(address indexed account, uint8 band, uint256 tokenId);

    constructor(address verifier_) ERC721("Nexor Credit", "NXRC") {
        require(verifier_ != address(0), "NexorCredit: verifier required");
        verifier = IGroth16Verifier(verifier_);
    }

    function creditBandOf(address account) external view returns (uint8) {
        return _creditBand[account];
    }

    function mintCreditBand(
        address to,
        uint8 band,
        uint[2] calldata a,
        uint[2][2] calldata b,
        uint[2] calldata c,
        uint[2] calldata pubSignals
    ) external returns (uint256 tokenId) {
        require(to != address(0), "NexorCredit: invalid recipient");
        require(_creditBand[to] == 0, "NexorCredit: already minted");
        require(band >= 1 && band <= 4, "NexorCredit: invalid band");
        require(verifier.verifyProof(a, b, c, pubSignals), "Invalid proof");
        require(pubSignals[0] == uint256(band), "NexorCredit: band mismatch");

        tokenId = uint256(uint160(to));
        _creditBand[to] = band;

        _safeMint(to, tokenId);
        emit Locked(tokenId);
        emit CreditBandMinted(to, band, tokenId);
    }

    function supportsInterface(bytes4 interfaceId) public view virtual override returns (bool) {
        return interfaceId == type(IERC5192).interfaceId || super.supportsInterface(interfaceId);
    }
}

