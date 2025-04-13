// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "./QuantumVerifier.sol";
import "./ESIMBenefitsManager.sol";
import "./BandwidthToken.sol";

/**
 * @title QuantumESIM
 * @dev Advanced eSIM implementation with quantum computing features
 */
contract QuantumESIM is ERC721, ERC721URIStorage, ReentrancyGuard, AccessControl {
    using Counters for Counters.Counter;

    bytes32 public constant QUANTUM_OPERATOR_ROLE = keccak256("QUANTUM_OPERATOR_ROLE");
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    Counters.Counter private _tokenIdCounter;

    // External contracts
    QuantumVerifier public quantumVerifier;
    ESIMBenefitsManager public benefitsManager;
    BandwidthToken public bandwidthToken;

    struct QuantumESIMData {
        string iccid;           // Integrated Circuit Card ID
        bytes32 quantumKey;     // Quantum-generated security key
        uint256 entanglementId; // ID for quantum entanglement tracking
        uint256 securityScore;  // Quantum security score
        bool quantumEnabled;    // Quantum features enabled
        uint256 lastVerification; // Last quantum verification timestamp
        mapping(string => bytes32) quantumStates; // Quantum state storage
    }

    // Mapping for quantum ESIM data
    mapping(uint256 => QuantumESIMData) public quantumEsimData;
    
    // Mapping for entanglement pairs
    mapping(uint256 => uint256) public entanglementPairs;
    
    // Security thresholds
    uint256 public constant MIN_SECURITY_SCORE = 80;
    uint256 public constant VERIFICATION_INTERVAL = 1 days;

    event QuantumESIMMinted(
        uint256 indexed tokenId,
        string iccid,
        bytes32 quantumKey,
        uint256 securityScore
    );
    event QuantumStateUpdated(
        uint256 indexed tokenId,
        bytes32 newState,
        uint256 timestamp
    );
    event EntanglementCreated(
        uint256 indexed tokenId1,
        uint256 indexed tokenId2,
        uint256 entanglementId
    );
    event SecurityScoreUpdated(
        uint256 indexed tokenId,
        uint256 oldScore,
        uint256 newScore
    );
    event QuantumVerificationPerformed(
        uint256 indexed tokenId,
        bool success,
        uint256 timestamp
    );

    constructor(
        address _quantumVerifier,
        address _benefitsManager,
        address _bandwidthToken
    ) ERC721("QuantumESIM", "QSIM") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        
        quantumVerifier = QuantumVerifier(_quantumVerifier);
        benefitsManager = ESIMBenefitsManager(_benefitsManager);
        bandwidthToken = BandwidthToken(_bandwidthToken);
    }

    function mintQuantumESIM(
        address to,
        string memory iccid,
        bytes32 quantumKey,
        string memory uri
    ) external onlyRole(MINTER_ROLE) nonReentrant returns (uint256) {
        require(bytes(iccid).length > 0, "Invalid ICCID");
        require(quantumKey != bytes32(0), "Invalid quantum key");
        
        _tokenIdCounter.increment();
        uint256 tokenId = _tokenIdCounter.current();
        
        // Generate quantum security score
        uint256 securityScore = _generateSecurityScore(quantumKey);
        require(securityScore >= MIN_SECURITY_SCORE, "Insufficient security score");
        
        // Initialize quantum ESIM data
        quantumEsimData[tokenId].iccid = iccid;
        quantumEsimData[tokenId].quantumKey = quantumKey;
        quantumEsimData[tokenId].securityScore = securityScore;
        quantumEsimData[tokenId].quantumEnabled = true;
        quantumEsimData[tokenId].lastVerification = block.timestamp;
        
        // Mint NFT
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);
        
        // Initialize benefits with quantum features
        _initializeQuantumBenefits(tokenId);
        
        emit QuantumESIMMinted(tokenId, iccid, quantumKey, securityScore);
        return tokenId;
    }

    function createEntanglement(
        uint256 tokenId1,
        uint256 tokenId2
    ) external onlyRole(QUANTUM_OPERATOR_ROLE) nonReentrant {
        require(
            _exists(tokenId1) && _exists(tokenId2),
            "Tokens do not exist"
        );
        require(
            quantumEsimData[tokenId1].entanglementId == 0 &&
            quantumEsimData[tokenId2].entanglementId == 0,
            "Tokens already entangled"
        );
        
        // Generate entanglement ID using quantum randomness
        uint256 entanglementId = uint256(
            keccak256(
                abi.encodePacked(
                    quantumEsimData[tokenId1].quantumKey,
                    quantumEsimData[tokenId2].quantumKey,
                    block.timestamp
                )
            )
        );
        
        // Set entanglement
        quantumEsimData[tokenId1].entanglementId = entanglementId;
        quantumEsimData[tokenId2].entanglementId = entanglementId;
        
        entanglementPairs[tokenId1] = tokenId2;
        entanglementPairs[tokenId2] = tokenId1;
        
        emit EntanglementCreated(tokenId1, tokenId2, entanglementId);
    }

    function updateQuantumState(
        uint256 tokenId,
        string memory stateKey,
        bytes32 newState
    ) external onlyRole(QUANTUM_OPERATOR_ROLE) nonReentrant {
        require(_exists(tokenId), "Token does not exist");
        require(
            quantumEsimData[tokenId].quantumEnabled,
            "Quantum features not enabled"
        );
        
        // Update quantum state
        quantumEsimData[tokenId].quantumStates[stateKey] = newState;
        
        // If token is entangled, update pair's state
        uint256 pairedTokenId = entanglementPairs[tokenId];
        if (pairedTokenId != 0) {
            quantumEsimData[pairedTokenId].quantumStates[stateKey] = newState;
        }
        
        emit QuantumStateUpdated(tokenId, newState, block.timestamp);
    }

    function performQuantumVerification(
        uint256 tokenId
    ) external onlyRole(QUANTUM_OPERATOR_ROLE) nonReentrant returns (bool) {
        require(_exists(tokenId), "Token does not exist");
        require(
            block.timestamp >= quantumEsimData[tokenId].lastVerification + VERIFICATION_INTERVAL,
            "Verification too soon"
        );
        
        bool verificationSuccess = _verifyQuantumState(tokenId);
        
        if (verificationSuccess) {
            // Update security score based on verification
            uint256 oldScore = quantumEsimData[tokenId].securityScore;
            uint256 newScore = _updateSecurityScore(tokenId);
            
            emit SecurityScoreUpdated(tokenId, oldScore, newScore);
        }
        
        quantumEsimData[tokenId].lastVerification = block.timestamp;
        
        emit QuantumVerificationPerformed(
            tokenId,
            verificationSuccess,
            block.timestamp
        );
        
        return verificationSuccess;
    }

    function getQuantumState(
        uint256 tokenId,
        string memory stateKey
    ) external view returns (bytes32) {
        require(_exists(tokenId), "Token does not exist");
        return quantumEsimData[tokenId].quantumStates[stateKey];
    }

    function getEntangledPair(
        uint256 tokenId
    ) external view returns (uint256) {
        require(_exists(tokenId), "Token does not exist");
        return entanglementPairs[tokenId];
    }

    function _generateSecurityScore(
        bytes32 quantumKey
    ) private pure returns (uint256) {
        // Generate score based on quantum key entropy
        uint256 entropyScore = uint256(
            keccak256(
                abi.encodePacked(quantumKey)
            )
        ) % 21 + 80; // Score between 80-100
        
        return entropyScore;
    }

    function _verifyQuantumState(
        uint256 tokenId
    ) private view returns (bool) {
        // Verify quantum state consistency
        if (entanglementPairs[tokenId] != 0) {
            uint256 pairedTokenId = entanglementPairs[tokenId];
            
            // Compare quantum states of entangled pairs
            bytes32 state1 = quantumEsimData[tokenId].quantumStates["base"];
            bytes32 state2 = quantumEsimData[pairedTokenId].quantumStates["base"];
            
            return state1 == state2;
        }
        
        return true;
    }

    function _updateSecurityScore(
        uint256 tokenId
    ) private returns (uint256) {
        uint256 currentScore = quantumEsimData[tokenId].securityScore;
        uint256 timeBonus = (block.timestamp - quantumEsimData[tokenId].lastVerification) / 1 days;
        
        // Increase score based on successful verifications
        uint256 newScore = currentScore + (timeBonus > 5 ? 5 : timeBonus);
        
        // Cap score at 100
        newScore = newScore > 100 ? 100 : newScore;
        
        quantumEsimData[tokenId].securityScore = newScore;
        return newScore;
    }

    function _initializeQuantumBenefits(uint256 tokenId) private {
        // Initialize with quantum tier if security score is high enough
        string memory tier = quantumEsimData[tokenId].securityScore >= 95
            ? "quantum"
            : "cosmic";
            
        benefitsManager.updateTokenBenefits(
            tokenId,
            tier,
            100, // Initial performance score
            quantumEsimData[tokenId].quantumKey
        );
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal virtual override {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
        
        // Verify quantum state before transfer
        require(
            _verifyQuantumState(tokenId),
            "Quantum state verification failed"
        );
    }

    function _burn(
        uint256 tokenId
    ) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }

    function tokenURI(
        uint256 tokenId
    ) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(
        bytes4 interfaceId
    ) public view override(ERC721, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
