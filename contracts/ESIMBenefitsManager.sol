// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "./EnhancedDynamicESIMNFT.sol";

contract ESIMBenefitsManager is Ownable {
    EnhancedDynamicESIMNFT public esimNFT;
    
    // Benefit multipliers based on rarity (in basis points, 100 = 1%)
    uint256 private constant LEGENDARY_MULTIPLIER = 500;  // 5x
    uint256 private constant EPIC_MULTIPLIER = 300;      // 3x
    uint256 private constant RARE_MULTIPLIER = 200;      // 2x
    uint256 private constant COMMON_MULTIPLIER = 100;    // 1x

    // Theme-specific benefits
    struct ThemeBenefits {
        bool priorityRouting;      // Better network routing
        bool dataRollover;        // Unused data rolls over
        bool peakHourPriority;    // Priority during peak hours
        uint256 speedBoost;       // Speed boost in percentage
        bool quantumEncryption;   // Access to quantum encryption
    }

    struct QuantumBonus {
        uint256 encryptionStrength;    // Quantum encryption strength bonus (1-100)
        uint256 routingPriority;       // Priority in quantum-secured routes
        bool quantumResistance;        // Access to quantum-resistant features
        uint256 bandwidthMultiplier;   // Additional bandwidth multiplier
    }
    
    mapping(string => ThemeBenefits) public themeBenefits;
    mapping(uint256 => uint256) public tokenBonusPoints;
    mapping(uint256 => QuantumBonus) public quantumBonuses;

    event BenefitsUpdated(uint256 indexed tokenId, uint256 multiplier);
    event ThemeBenefitsConfigured(string theme);
    event BonusPointsEarned(uint256 indexed tokenId, uint256 points);
    event QuantumBonusUpdated(uint256 indexed tokenId, uint256 encryptionStrength, uint256 routingPriority);

    constructor(address _esimNFTAddress) {
        esimNFT = EnhancedDynamicESIMNFT(_esimNFTAddress);
        _initializeThemeBenefits();
    }

    function _initializeThemeBenefits() private {
        // Quantum theme benefits
        themeBenefits["quantum"] = ThemeBenefits({
            priorityRouting: true,
            dataRollover: true,
            peakHourPriority: true,
            speedBoost: 50,        // 50% speed boost
            quantumEncryption: true
        });

        // Cosmic theme benefits
        themeBenefits["cosmic"] = ThemeBenefits({
            priorityRouting: true,
            dataRollover: true,
            peakHourPriority: false,
            speedBoost: 30,        // 30% speed boost
            quantumEncryption: false
        });

        // Cyber theme benefits
        themeBenefits["cyber"] = ThemeBenefits({
            priorityRouting: true,
            dataRollover: false,
            peakHourPriority: true,
            speedBoost: 40,        // 40% speed boost
            quantumEncryption: false
        });

        // Other themes...
        themeBenefits["nebula"] = ThemeBenefits({
            priorityRouting: false,
            dataRollover: true,
            peakHourPriority: false,
            speedBoost: 20,        // 20% speed boost
            quantumEncryption: false
        });

        themeBenefits["matrix"] = ThemeBenefits({
            priorityRouting: true,
            dataRollover: false,
            peakHourPriority: false,
            speedBoost: 25,        // 25% speed boost
            quantumEncryption: true
        });
    }

    function calculateBenefits(uint256 tokenId) public view returns (
        uint256 speedMultiplier,
        bool hasPriorityRouting,
        bool hasDataRollover,
        bool hasPeakHourPriority,
        bool hasQuantumEncryption,
        uint256 bonusPoints
    ) {
        EnhancedDynamicESIMNFT.ESIM memory esim = esimNFT.esims(tokenId);
        require(esim.id == tokenId, "eSIM not found");

        // Get theme benefits
        ThemeBenefits memory themeBenefit = themeBenefits[esim.designTheme];
        
        // Calculate rarity multiplier
        uint256 rarityMultiplier;
        if (esim.rarity >= 950) rarityMultiplier = LEGENDARY_MULTIPLIER;
        else if (esim.rarity >= 850) rarityMultiplier = EPIC_MULTIPLIER;
        else if (esim.rarity >= 700) rarityMultiplier = RARE_MULTIPLIER;
        else rarityMultiplier = COMMON_MULTIPLIER;

        // Apply rarity multiplier to speed boost
        speedMultiplier = (themeBenefit.speedBoost * rarityMultiplier) / 100;

        return (
            speedMultiplier,
            themeBenefit.priorityRouting,
            themeBenefit.dataRollover,
            themeBenefit.peakHourPriority,
            themeBenefit.quantumEncryption,
            tokenBonusPoints[tokenId]
        );
    }

    function calculateQuantumBenefits(uint256 tokenId) public view returns (
        uint256 totalSpeedMultiplier,
        uint256 encryptionLevel,
        uint256 routingPriority,
        bool hasQuantumResistance
    ) {
        EnhancedDynamicESIMNFT.ESIM memory esim = esimNFT.esims(tokenId);
        ThemeBenefits memory themeBenefit = themeBenefits[esim.designTheme];
        QuantumBonus memory qBonus = quantumBonuses[tokenId];
        
        // Calculate base multiplier from theme and rarity
        uint256 baseMultiplier = _calculateBaseMultiplier(esim.rarity, themeBenefit.speedBoost);
        
        // Apply quantum bonuses
        totalSpeedMultiplier = baseMultiplier + qBonus.bandwidthMultiplier;
        encryptionLevel = qBonus.encryptionStrength;
        routingPriority = qBonus.routingPriority;
        hasQuantumResistance = qBonus.quantumResistance;
    }

    function earnBonusPoints(uint256 tokenId, uint256 dataUsed) external onlyOwner {
        EnhancedDynamicESIMNFT.ESIM memory esim = esimNFT.esims(tokenId);
        require(esim.id == tokenId, "eSIM not found");

        // Calculate points based on data usage and rarity
        uint256 points = (dataUsed * esim.rarity) / 1000;
        tokenBonusPoints[tokenId] += points;

        emit BonusPointsEarned(tokenId, points);
    }

    function updateThemeBenefits(
        string memory theme,
        bool priorityRouting,
        bool dataRollover,
        bool peakHourPriority,
        uint256 speedBoost,
        bool quantumEncryption
    ) external onlyOwner {
        themeBenefits[theme] = ThemeBenefits({
            priorityRouting: priorityRouting,
            dataRollover: dataRollover,
            peakHourPriority: peakHourPriority,
            speedBoost: speedBoost,
            quantumEncryption: quantumEncryption
        });

        emit ThemeBenefitsConfigured(theme);
    }

    function updateQuantumBonus(
        uint256 tokenId,
        uint256 encryptionStrength,
        uint256 routingPriority,
        bool quantumResistance,
        uint256 bandwidthMultiplier
    ) external onlyOwner {
        require(encryptionStrength <= 100, "Invalid encryption strength");
        require(routingPriority <= 100, "Invalid routing priority");
        
        quantumBonuses[tokenId] = QuantumBonus({
            encryptionStrength: encryptionStrength,
            routingPriority: routingPriority,
            quantumResistance: quantumResistance,
            bandwidthMultiplier: bandwidthMultiplier
        });
        
        emit QuantumBonusUpdated(tokenId, encryptionStrength, routingPriority);
    }

    function redeemBonusPoints(uint256 tokenId, uint256 points) external {
        EnhancedDynamicESIMNFT.ESIM memory esim = esimNFT.esims(tokenId);
        require(esim.owner == msg.sender, "Not the token owner");
        require(tokenBonusPoints[tokenId] >= points, "Insufficient points");

        tokenBonusPoints[tokenId] -= points;
        // Implementation of rewards redemption would go here
        // Could include: extra data, temporary speed boosts, etc.
    }

    function _calculateBaseMultiplier(uint256 rarity, uint256 themeBoost) internal pure returns (uint256) {
        // Rarity tiers: Legendary (950-1000), Epic (850-949), Rare (700-849), Common (1-699)
        uint256 rarityMultiplier;
        if (rarity >= 950) rarityMultiplier = LEGENDARY_MULTIPLIER;      // 5x
        else if (rarity >= 850) rarityMultiplier = EPIC_MULTIPLIER;      // 3x
        else if (rarity >= 700) rarityMultiplier = RARE_MULTIPLIER;      // 2x
        else rarityMultiplier = COMMON_MULTIPLIER;                       // 1x
        
        return (themeBoost * rarityMultiplier) / 100;
    }
}