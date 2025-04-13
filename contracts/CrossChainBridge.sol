// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./EnhancedDynamicESIMNFT.sol";
import "./QuantumVerifier.sol";

contract CrossChainBridge is ReentrancyGuard, Ownable {
    struct BridgeTransaction {
        uint256 tokenId;
        address sourceChain;
        address targetChain;
        bytes32 quantumProof;
        uint256 timestamp;
        bool isCompleted;
    }

    EnhancedDynamicESIMNFT public sourceNFT;
    QuantumVerifier public verifier;
    
    mapping(bytes32 => BridgeTransaction) public bridgeTransactions;
    mapping(address => mapping(uint256 => bool)) public tokenLocks;
    
    uint256 public bridgingCooldown = 1 hours;
    uint256 public constant QUANTUM_ENTROPY_THRESHOLD = 95;
    
    event TokenLocked(uint256 indexed tokenId, address indexed sourceChain, bytes32 quantumProof);
    event TokenUnlocked(uint256 indexed tokenId, address indexed targetChain, bytes32 quantumProof);
    event BridgeInitiated(bytes32 indexed txHash, uint256 indexed tokenId, address targetChain);
    event BridgeCompleted(bytes32 indexed txHash, uint256 indexed tokenId, address targetChain);
    
    constructor(address _nftContract, address _verifierContract) {
        sourceNFT = EnhancedDynamicESIMNFT(_nftContract);
        verifier = QuantumVerifier(_verifierContract);
    }
    
    function initiateBridging(
        uint256 tokenId,
        address targetChain,
        bytes32 quantumProof
    ) external nonReentrant {
        require(sourceNFT.ownerOf(tokenId) == msg.sender, "Not token owner");
        require(!tokenLocks[msg.sender][tokenId], "Token already locked");
        require(verifier.verifyQuantumProof(quantumProof), "Invalid quantum proof");
        
        bytes32 txHash = generateTransactionHash(tokenId, targetChain, quantumProof);
        
        bridgeTransactions[txHash] = BridgeTransaction({
            tokenId: tokenId,
            sourceChain: msg.sender,
            targetChain: targetChain,
            quantumProof: quantumProof,
            timestamp: block.timestamp,
            isCompleted: false
        });
        
        // Lock the token
        tokenLocks[msg.sender][tokenId] = true;
        sourceNFT.transferFrom(msg.sender, address(this), tokenId);
        
        emit TokenLocked(tokenId, msg.sender, quantumProof);
        emit BridgeInitiated(txHash, tokenId, targetChain);
    }
    
    function completeBridging(
        bytes32 txHash,
        bytes32 newQuantumProof
    ) external nonReentrant {
        BridgeTransaction storage bridgeTx = bridgeTransactions[txHash];
        require(!bridgeTx.isCompleted, "Bridge already completed");
        require(block.timestamp >= bridgeTx.timestamp + bridgingCooldown, "Cooldown period");
        require(verifier.verifyQuantumProof(newQuantumProof), "Invalid quantum proof");
        
        // Verify quantum entropy requirements
        require(
            verifier.calculateEntropyScore(newQuantumProof) >= QUANTUM_ENTROPY_THRESHOLD,
            "Insufficient quantum entropy"
        );
        
        bridgeTx.isCompleted = true;
        tokenLocks[bridgeTx.sourceChain][bridgeTx.tokenId] = false;
        
        // Transfer token to target chain
        sourceNFT.transferFrom(address(this), bridgeTx.targetChain, bridgeTx.tokenId);
        
        emit TokenUnlocked(bridgeTx.tokenId, bridgeTx.targetChain, newQuantumProof);
        emit BridgeCompleted(txHash, bridgeTx.tokenId, bridgeTx.targetChain);
    }
    
    function generateTransactionHash(
        uint256 tokenId,
        address targetChain,
        bytes32 quantumProof
    ) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(tokenId, targetChain, quantumProof));
    }
    
    function updateBridgingCooldown(uint256 newCooldown) external onlyOwner {
        require(newCooldown > 0, "Invalid cooldown period");
        bridgingCooldown = newCooldown;
    }
    
    function emergencyWithdraw(
        uint256 tokenId,
        address originalOwner
    ) external onlyOwner {
        require(tokenLocks[originalOwner][tokenId], "Token not locked");
        
        tokenLocks[originalOwner][tokenId] = false;
        sourceNFT.transferFrom(address(this), originalOwner, tokenId);
    }
}
