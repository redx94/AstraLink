// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

/**
 * @title QuantumVerifier
 * @dev Handles quantum signature verification and proof validation for eSIM NFTs
 */
contract QuantumVerifier is AccessControl, ReentrancyGuard, Pausable {
    using ECDSA for bytes32;
    using Counters for Counters.Counter;

    bytes32 public constant QUANTUM_VERIFIER_ROLE = keccak256("QUANTUM_VERIFIER_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");

    struct QuantumProof {
        bytes signature;
        bytes32 dataHash;
        uint256 timestamp;
        uint256 entropyScore;
        bool isVerified;
        address verifier;
    }

    struct VerificationRequest {
        bytes32 proofId;
        address requester;
        uint256 timestamp;
        bool isProcessed;
        bool isValid;
    }

    // Mapping from token ID to quantum proof
    mapping(uint256 => QuantumProof) public tokenProofs;
    
    // Mapping from hash to verification request
    mapping(bytes32 => VerificationRequest) public verificationRequests;
    
    // Counter for verification requests
    Counters.Counter private _requestIds;

    // Entropy threshold for quantum verification
    uint256 public minEntropyThreshold;
    
    // Verification timelock
    uint256 public verificationTimelock;
    
    // Maximum verification attempts
    uint256 public maxVerificationAttempts;

    event ProofSubmitted(uint256 indexed tokenId, bytes32 proofId, uint256 timestamp);
    event ProofVerified(uint256 indexed tokenId, bytes32 proofId, bool isValid);
    event VerificationRequested(bytes32 indexed requestId, address requester);
    event EntropyThresholdUpdated(uint256 oldThreshold, uint256 newThreshold);
    event TimelockUpdated(uint256 oldTimelock, uint256 newTimelock);
    event VerificationAttemptsUpdated(uint256 oldMax, uint256 newMax);

    constructor(
        uint256 _minEntropyThreshold,
        uint256 _verificationTimelock,
        uint256 _maxVerificationAttempts
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(QUANTUM_VERIFIER_ROLE, msg.sender);
        
        minEntropyThreshold = _minEntropyThreshold;
        verificationTimelock = _verificationTimelock;
        maxVerificationAttempts = _maxVerificationAttempts;
    }

    function submitProof(
        uint256 tokenId,
        bytes calldata signature,
        bytes32 dataHash,
        uint256 entropyScore
    ) external onlyRole(OPERATOR_ROLE) whenNotPaused nonReentrant returns (bytes32) {
        require(entropyScore >= minEntropyThreshold, "Insufficient entropy score");
        require(tokenProofs[tokenId].timestamp == 0, "Proof already exists");

        bytes32 proofId = keccak256(abi.encodePacked(
            tokenId,
            signature,
            dataHash,
            block.timestamp
        ));

        tokenProofs[tokenId] = QuantumProof({
            signature: signature,
            dataHash: dataHash,
            timestamp: block.timestamp,
            entropyScore: entropyScore,
            isVerified: false,
            verifier: address(0)
        });

        emit ProofSubmitted(tokenId, proofId, block.timestamp);
        return proofId;
    }

    function requestVerification(
        uint256 tokenId
    ) external whenNotPaused nonReentrant returns (bytes32) {
        require(tokenProofs[tokenId].timestamp > 0, "Proof does not exist");
        require(
            block.timestamp >= tokenProofs[tokenId].timestamp + verificationTimelock,
            "Verification timelock active"
        );

        bytes32 requestId = keccak256(abi.encodePacked(
            tokenId,
            msg.sender,
            block.timestamp
        ));

        verificationRequests[requestId] = VerificationRequest({
            proofId: requestId,
            requester: msg.sender,
            timestamp: block.timestamp,
            isProcessed: false,
            isValid: false
        });

        _requestIds.increment();
        emit VerificationRequested(requestId, msg.sender);
        return requestId;
    }

    function verifyProof(
        uint256 tokenId,
        bytes32 requestId,
        bool isValid
    ) external onlyRole(QUANTUM_VERIFIER_ROLE) whenNotPaused nonReentrant {
        require(tokenProofs[tokenId].timestamp > 0, "Proof does not exist");
        require(verificationRequests[requestId].timestamp > 0, "Request does not exist");
        require(!verificationRequests[requestId].isProcessed, "Request already processed");
        
        QuantumProof storage proof = tokenProofs[tokenId];
        proof.isVerified = isValid;
        proof.verifier = msg.sender;

        verificationRequests[requestId].isProcessed = true;
        verificationRequests[requestId].isValid = isValid;

        emit ProofVerified(tokenId, requestId, isValid);
    }

    function updateEntropyThreshold(
        uint256 newThreshold
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 oldThreshold = minEntropyThreshold;
        minEntropyThreshold = newThreshold;
        emit EntropyThresholdUpdated(oldThreshold, newThreshold);
    }

    function updateVerificationTimelock(
        uint256 newTimelock
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 oldTimelock = verificationTimelock;
        verificationTimelock = newTimelock;
        emit TimelockUpdated(oldTimelock, newTimelock);
    }

    function updateMaxVerificationAttempts(
        uint256 newMax
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 oldMax = maxVerificationAttempts;
        maxVerificationAttempts = newMax;
        emit VerificationAttemptsUpdated(oldMax, newMax);
    }

    function getProof(
        uint256 tokenId
    ) external view returns (
        bytes memory signature,
        bytes32 dataHash,
        uint256 timestamp,
        uint256 entropyScore,
        bool isVerified,
        address verifier
    ) {
        QuantumProof storage proof = tokenProofs[tokenId];
        return (
            proof.signature,
            proof.dataHash,
            proof.timestamp,
            proof.entropyScore,
            proof.isVerified,
            proof.verifier
        );
    }

    function getVerificationRequest(
        bytes32 requestId
    ) external view returns (
        bytes32 proofId,
        address requester,
        uint256 timestamp,
        bool isProcessed,
        bool isValid
    ) {
        VerificationRequest storage request = verificationRequests[requestId];
        return (
            request.proofId,
            request.requester,
            request.timestamp,
            request.isProcessed,
            request.isValid
        );
    }

    function getTotalRequests() external view returns (uint256) {
        return _requestIds.current();
    }

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
}
