// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "./QuantumVerifier.sol";

/**
 * @title ESIMBenefitsManager
 * @dev Manages benefits and features for eSIM NFTs with quantum security
 */
contract ESIMBenefitsManager is AccessControl, ReentrancyGuard, Pausable {
    using Counters for Counters.Counter;

    bytes32 public constant BENEFIT_MANAGER_ROLE = keccak256("BENEFIT_MANAGER_ROLE");
    bytes32 public constant QUANTUM_OPERATOR_ROLE = keccak256("QUANTUM_OPERATOR_ROLE");

    struct BenefitTier {
        string name;
        uint256 speedMultiplier;
        bool priorityRouting;
        bool dataRollover;
        bool peakHourPriority;
        bool quantumEncryption;
        uint256 bonusPointMultiplier;
        uint256 minRarityScore;
    }

    struct TokenBenefits {
        string currentTier;
        uint256 bonusPoints;
        uint256 performanceScore;
        uint256 lastUpdate;
        mapping(string => bool) activeFeatures;
        NetworkMetrics metrics;
    }

    struct NetworkMetrics {
        uint256 latency;
        uint256 reliability;
        uint256 congestionIndex;
        uint256 qosLevel;
        uint256 adaptabilityScore;
    }

    // Reference to QuantumVerifier contract
    QuantumVerifier public quantumVerifier;

    // Mapping of tier names to benefit tiers
    mapping(string => BenefitTier) public benefitTiers;
    
    // Mapping from token ID to benefits
    mapping(uint256 => TokenBenefits) public tokenBenefits;
    
    // Performance thresholds
    uint256 public minPerformanceScore = 50;
    uint256 public maxPerformanceScore = 100;
    uint256 public bonusPointThreshold = 1000;

    // Events
    event BenefitTierCreated(string name, uint256 minRarityScore);
    event BenefitTierUpdated(string name, uint256 newMinRarityScore);
    event TokenBenefitsUpdated(uint256 indexed tokenId, string tier, uint256 performanceScore);
    event BonusPointsEarned(uint256 indexed tokenId, uint256 points, uint256 multiplier);
    event NetworkMetricsUpdated(uint256 indexed tokenId, uint256 latency, uint256 reliability);
    event FeatureActivated(uint256 indexed tokenId, string feature);
    event FeatureDeactivated(uint256 indexed tokenId, string feature);

    constructor(address _quantumVerifier) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(BENEFIT_MANAGER_ROLE, msg.sender);
        quantumVerifier = QuantumVerifier(_quantumVerifier);
        
        // Initialize default benefit tiers
        _initializeDefaultTiers();
    }

    function createBenefitTier(
        string memory name,
        uint256 speedMultiplier,
        bool priorityRouting,
        bool dataRollover,
        bool peakHourPriority,
        bool quantumEncryption,
        uint256 bonusPointMultiplier,
        uint256 minRarityScore
    ) external onlyRole(BENEFIT_MANAGER_ROLE) {
        require(benefitTiers[name].minRarityScore == 0, "Tier already exists");
        
        benefitTiers[name] = BenefitTier({
            name: name,
            speedMultiplier: speedMultiplier,
            priorityRouting: priorityRouting,
            dataRollover: dataRollover,
            peakHourPriority: peakHourPriority,
            quantumEncryption: quantumEncryption,
            bonusPointMultiplier: bonusPointMultiplier,
            minRarityScore: minRarityScore
        });
        
        emit BenefitTierCreated(name, minRarityScore);
    }

    function updateTokenBenefits(
        uint256 tokenId,
        string memory tier,
        uint256 performanceScore,
        bytes32 quantumProof
    ) external onlyRole(QUANTUM_OPERATOR_ROLE) whenNotPaused nonReentrant {
        require(benefitTiers[tier].minRarityScore > 0, "Invalid tier");
        require(
            performanceScore >= minPerformanceScore && 
            performanceScore <= maxPerformanceScore,
            "Invalid performance score"
        );
        
        // Verify quantum proof
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        TokenBenefits storage benefits = tokenBenefits[tokenId];
        benefits.currentTier = tier;
        benefits.performanceScore = performanceScore;
        benefits.lastUpdate = block.timestamp;
        
        emit TokenBenefitsUpdated(tokenId, tier, performanceScore);
    }

    function earnBonusPoints(
        uint256 tokenId,
        uint256 dataUsed,
        bytes32 quantumProof
    ) external onlyRole(QUANTUM_OPERATOR_ROLE) whenNotPaused nonReentrant {
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        TokenBenefits storage benefits = tokenBenefits[tokenId];
        BenefitTier memory tier = benefitTiers[benefits.currentTier];
        
        // Calculate bonus points based on data usage and performance
        uint256 basePoints = (dataUsed * tier.bonusPointMultiplier) / 1000;
        uint256 performanceBonus = (basePoints * benefits.performanceScore) / 100;
        uint256 totalPoints = basePoints + performanceBonus;
        
        benefits.bonusPoints += totalPoints;
        
        emit BonusPointsEarned(tokenId, totalPoints, tier.bonusPointMultiplier);
    }

    function updateNetworkMetrics(
        uint256 tokenId,
        uint256 latency,
        uint256 reliability,
        uint256 congestionIndex,
        uint256 qosLevel,
        bytes32 quantumProof
    ) external onlyRole(QUANTUM_OPERATOR_ROLE) whenNotPaused nonReentrant {
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        TokenBenefits storage benefits = tokenBenefits[tokenId];
        
        benefits.metrics = NetworkMetrics({
            latency: latency,
            reliability: reliability,
            congestionIndex: congestionIndex,
            qosLevel: qosLevel,
            adaptabilityScore: _calculateAdaptabilityScore(latency, reliability, congestionIndex)
        });
        
        // Update performance score based on metrics
        benefits.performanceScore = _calculatePerformanceScore(benefits.metrics);
        
        emit NetworkMetricsUpdated(tokenId, latency, reliability);
    }

    function activateFeature(
        uint256 tokenId,
        string memory feature,
        bytes32 quantumProof
    ) external onlyRole(QUANTUM_OPERATOR_ROLE) whenNotPaused nonReentrant {
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        TokenBenefits storage benefits = tokenBenefits[tokenId];
        benefits.activeFeatures[feature] = true;
        
        emit FeatureActivated(tokenId, feature);
    }

    function deactivateFeature(
        uint256 tokenId,
        string memory feature,
        bytes32 quantumProof
    ) external onlyRole(QUANTUM_OPERATOR_ROLE) whenNotPaused nonReentrant {
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        TokenBenefits storage benefits = tokenBenefits[tokenId];
        benefits.activeFeatures[feature] = false;
        
        emit FeatureDeactivated(tokenId, feature);
    }

    function getTokenBenefits(
        uint256 tokenId
    ) external view returns (
        string memory tier,
        uint256 bonusPoints,
        uint256 performanceScore,
        uint256 lastUpdate,
        NetworkMetrics memory metrics
    ) {
        TokenBenefits storage benefits = tokenBenefits[tokenId];
        return (
            benefits.currentTier,
            benefits.bonusPoints,
            benefits.performanceScore,
            benefits.lastUpdate,
            benefits.metrics
        );
    }

    function isFeatureActive(
        uint256 tokenId,
        string memory feature
    ) external view returns (bool) {
        return tokenBenefits[tokenId].activeFeatures[feature];
    }

    function _initializeDefaultTiers() private {
        // Quantum tier
        createBenefitTier(
            "quantum",
            50,  // 50% speed boost
            true,
            true,
            true,
            true,
            5,    // 5x bonus points
            950   // 95th percentile rarity
        );

        // Cosmic tier
        createBenefitTier(
            "cosmic",
            30,  // 30% speed boost
            true,
            true,
            false,
            false,
            3,    // 3x bonus points
            850   // 85th percentile rarity
        );

        // Cyber tier
        createBenefitTier(
            "cyber",
            20,  // 20% speed boost
            true,
            false,
            false,
            false,
            2,    // 2x bonus points
            700   // 70th percentile rarity
        );
    }

    function _verifyQuantumProof(
        uint256 tokenId,
        bytes32 proofId
    ) private view returns (bool) {
        (,,,,bool isVerified,) = quantumVerifier.getProof(tokenId);
        return isVerified;
    }

    function _calculateAdaptabilityScore(
        uint256 latency,
        uint256 reliability,
        uint256 congestionIndex
    ) private pure returns (uint256) {
        uint256 latencyScore = latency <= 100 ? 100 - latency : 0;
        uint256 reliabilityScore = reliability;
        uint256 congestionScore = congestionIndex <= 50 ? 100 - (congestionIndex * 2) : 0;
        
        return (latencyScore + reliabilityScore + congestionScore) / 3;
    }

    function _calculatePerformanceScore(
        NetworkMetrics memory metrics
    ) private pure returns (uint256) {
        uint256 baseScore = (
            metrics.reliability * 40 +
            (100 - metrics.latency) * 30 +
            (100 - metrics.congestionIndex) * 30
        ) / 100;
        
        return baseScore;
    }

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
}