// SPDX-License-Identifier: MIT
/*
AstraLink - Enhanced Dynamic eSIM NFT Contract
=========================================

This smart contract implements NFT-based eSIM management with dynamic bandwidth
allocation and quantum-secure signature verification.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
See LICENSE file for licensing information.
*/

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title EnhancedDynamicESIMNFT
 * @dev Enhanced ESIM NFT contract with bandwidth management and quantum security
 */
contract EnhancedDynamicESIMNFT is ERC721, Ownable, ReentrancyGuard, Pausable {
    using Counters for Counters.Counter;

    Counters.Counter private _tokenIds;
    uint256 private constant MAX_BANDWIDTH = 1000000; // Maximum bandwidth units
    uint256 private constant RATE_LIMIT_PERIOD = 1 hours;
    uint256 private constant MAX_MINTS_PER_PERIOD = 100;

    struct ESIM {
        uint256 id;
        address owner;
        string status;
        string metadata;
        uint256 bandwidth;
        uint256 lastUpdated;
        bytes32 quantumSignature;
        uint256 activationTimestamp;
        bool isActive;
    }

    mapping(uint256 => ESIM) private esims;
    mapping(address => uint256) private mintingHistory;
    mapping(address => uint256) private lastMintTimestamp;
    mapping(bytes32 => bool) private usedQuantumSignatures;

    event ESIMMinted(uint256 indexed tokenId, address indexed owner, uint256 bandwidth);
    event ESIMStatusUpdated(uint256 indexed tokenId, string newStatus);
    event BandwidthAllocated(uint256 indexed tokenId, uint256 amount);
    event ESIMActivated(uint256 indexed tokenId, uint256 timestamp);
    event ESIMDeactivated(uint256 indexed tokenId, uint256 timestamp);

    modifier rateLimited() {
        require(
            block.timestamp - lastMintTimestamp[msg.sender] >= RATE_LIMIT_PERIOD ||
            mintingHistory[msg.sender] < MAX_MINTS_PER_PERIOD,
            "Rate limit exceeded"
        );
        _;
    }

    modifier validQuantumSignature(bytes32 signature) {
        require(!usedQuantumSignatures[signature], "Quantum signature already used");
        usedQuantumSignatures[signature] = true;
        _;
    }

    constructor() ERC721("DynamicESIMNFT", "DESIM") {}

    function mintESIM(
        address to,
        string memory metadata,
        uint256 initialBandwidth,
        bytes32 quantumSignature
    ) 
        external
        onlyOwner
        nonReentrant
        rateLimited
        validQuantumSignature(quantumSignature)
        returns (uint256)
    {
        require(to != address(0), "Invalid address");
        require(initialBandwidth <= MAX_BANDWIDTH, "Exceeds maximum bandwidth");

        _tokenIds.increment();
        uint256 newTokenId = _tokenIds.current();

        _safeMint(to, newTokenId);
        
        esims[newTokenId] = ESIM({
            id: newTokenId,
            owner: to,
            status: "Pending",
            metadata: metadata,
            bandwidth: initialBandwidth,
            lastUpdated: block.timestamp,
            quantumSignature: quantumSignature,
            activationTimestamp: 0,
            isActive: false
        });

        mintingHistory[msg.sender]++;
        lastMintTimestamp[msg.sender] = block.timestamp;

        emit ESIMMinted(newTokenId, to, initialBandwidth);
        return newTokenId;
    }

    function activateESIM(uint256 tokenId) 
        external 
        nonReentrant 
        onlyOwner 
    {
        require(_exists(tokenId), "ESIM does not exist");
        require(!esims[tokenId].isActive, "ESIM already active");

        esims[tokenId].isActive = true;
        esims[tokenId].status = "Active";
        esims[tokenId].activationTimestamp = block.timestamp;

        emit ESIMActivated(tokenId, block.timestamp);
    }

    function deactivateESIM(uint256 tokenId) 
        external 
        nonReentrant 
        onlyOwner 
    {
        require(_exists(tokenId), "ESIM does not exist");
        require(esims[tokenId].isActive, "ESIM not active");

        esims[tokenId].isActive = false;
        esims[tokenId].status = "Inactive";

        emit ESIMDeactivated(tokenId, block.timestamp);
    }

    function allocateBandwidth(uint256 tokenId, uint256 amount) 
        external 
        nonReentrant 
        onlyOwner 
    {
        require(_exists(tokenId), "ESIM does not exist");
        require(esims[tokenId].isActive, "ESIM not active");
        require(amount <= MAX_BANDWIDTH, "Exceeds maximum bandwidth");

        esims[tokenId].bandwidth = amount;
        esims[tokenId].lastUpdated = block.timestamp;

        emit BandwidthAllocated(tokenId, amount);
    }

    function updateMetadata(uint256 tokenId, string memory newMetadata) 
        external 
        nonReentrant 
    {
        require(ownerOf(tokenId) == msg.sender, "Not the owner");
        require(_exists(tokenId), "ESIM does not exist");

        esims[tokenId].metadata = newMetadata;
    }

    function getESIM(uint256 tokenId) 
        external 
        view 
        returns (ESIM memory) 
    {
        require(_exists(tokenId), "ESIM does not exist");
        return esims[tokenId];
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal override whenNotPaused {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
    }
}
