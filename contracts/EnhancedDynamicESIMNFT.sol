// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "./QuantumVerifier.sol";
import "./ESIMBenefitsManager.sol";

/**
 * @title EnhancedDynamicESIMNFT
 * @dev Advanced eSIM NFT implementation with quantum security and dynamic features
 */
contract EnhancedDynamicESIMNFT is 
    ERC721, 
    ERC721Enumerable, 
    ERC721URIStorage, 
    ReentrancyGuard, 
    AccessControl 
{
    using Counters for Counters.Counter;

    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant QUANTUM_OPERATOR_ROLE = keccak256("QUANTUM_OPERATOR_ROLE");

    Counters.Counter private _tokenIdCounter;
    
    // External contract references
    QuantumVerifier public quantumVerifier;
    ESIMBenefitsManager public benefitsManager;

    struct ESIMData {
        string carrier;
        uint256 bandwidth;
        uint256 validUntil;
        string theme;
        uint256 rarityScore;
        bytes32 quantumProof;
        bool active;
    }

    // Mapping from token ID to ESIM data
    mapping(uint256 => ESIMData) public esimData;
    
    // Mapping for quantum-secure activation codes
    mapping(uint256 => bytes32) private _activationCodes;
    
    // Carrier bandwidth limits
    mapping(string => uint256) public carrierBandwidthLimits;
    
    // Theme multipliers for rarity
    mapping(string => uint256) public themeMultipliers;

    // Events
    event ESIMMinted(
        uint256 indexed tokenId,
        address indexed owner,
        string carrier,
        uint256 bandwidth
    );
    event ESIMActivated(uint256 indexed tokenId, bytes32 quantumProof);
    event ESIMDeactivated(uint256 indexed tokenId, bytes32 deactivationProof);
    event BandwidthUpdated(
        uint256 indexed tokenId,
        uint256 oldBandwidth,
        uint256 newBandwidth
    );
    event ThemeUpdated(uint256 indexed tokenId, string newTheme);
    event CarrierUpdated(uint256 indexed tokenId, string newCarrier);

    constructor(
        address _quantumVerifier,
        address _benefitsManager
    ) ERC721("DynamicESIM", "ESIM") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        
        quantumVerifier = QuantumVerifier(_quantumVerifier);
        benefitsManager = ESIMBenefitsManager(_benefitsManager);
        
        _initializeThemeMultipliers();
    }

    function mintESIM(
        address to,
        string memory carrier,
        uint256 bandwidth,
        string memory theme,
        string memory uri,
        bytes32 quantumProof
    ) external onlyRole(MINTER_ROLE) nonReentrant returns (uint256) {
        require(bandwidth <= carrierBandwidthLimits[carrier], "Bandwidth exceeds limit");
        require(themeMultipliers[theme] > 0, "Invalid theme");
        
        // Increment token ID
        _tokenIdCounter.increment();
        uint256 tokenId = _tokenIdCounter.current();
        
        // Calculate rarity score
        uint256 rarityScore = _calculateRarityScore(bandwidth, theme);
        
        // Create ESIM data
        esimData[tokenId] = ESIMData({
            carrier: carrier,
            bandwidth: bandwidth,
            validUntil: block.timestamp + 365 days,
            theme: theme,
            rarityScore: rarityScore,
            quantumProof: quantumProof,
            active: false
        });
        
        // Mint NFT
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, uri);
        
        // Submit quantum proof
        quantumVerifier.submitProof(
            tokenId,
            abi.encodePacked(quantumProof),
            keccak256(abi.encodePacked(tokenId, carrier, bandwidth)),
            rarityScore
        );
        
        emit ESIMMinted(tokenId, to, carrier, bandwidth);
        return tokenId;
    }

    function activateESIM(
        uint256 tokenId,
        bytes32 activationCode,
        bytes32 quantumProof
    ) external nonReentrant {
        require(_isApprovedOrOwner(_msgSender(), tokenId), "Not approved");
        require(!esimData[tokenId].active, "Already activated");
        require(block.timestamp <= esimData[tokenId].validUntil, "ESIM expired");
        require(
            _verifyActivationCode(tokenId, activationCode),
            "Invalid activation code"
        );
        
        // Verify quantum proof
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        ESIMData storage esim = esimData[tokenId];
        esim.active = true;
        esim.quantumProof = quantumProof;
        
        // Initialize benefits
        _initializeTokenBenefits(tokenId);
        
        emit ESIMActivated(tokenId, quantumProof);
    }

    function deactivateESIM(
        uint256 tokenId,
        bytes32 deactivationProof
    ) external nonReentrant {
        require(_isApprovedOrOwner(_msgSender(), tokenId), "Not approved");
        require(esimData[tokenId].active, "Not activated");
        
        // Verify quantum proof
        require(
            _verifyQuantumProof(tokenId, deactivationProof),
            "Invalid deactivation proof"
        );
        
        ESIMData storage esim = esimData[tokenId];
        esim.active = false;
        esim.quantumProof = deactivationProof;
        
        emit ESIMDeactivated(tokenId, deactivationProof);
    }

    function updateBandwidth(
        uint256 tokenId,
        uint256 newBandwidth,
        bytes32 quantumProof
    ) external onlyRole(QUANTUM_OPERATOR_ROLE) nonReentrant {
        require(_exists(tokenId), "Token does not exist");
        require(
            newBandwidth <= carrierBandwidthLimits[esimData[tokenId].carrier],
            "Bandwidth exceeds limit"
        );
        
        // Verify quantum proof
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        uint256 oldBandwidth = esimData[tokenId].bandwidth;
        esimData[tokenId].bandwidth = newBandwidth;
        
        // Update rarity score
        esimData[tokenId].rarityScore = _calculateRarityScore(
            newBandwidth,
            esimData[tokenId].theme
        );
        
        emit BandwidthUpdated(tokenId, oldBandwidth, newBandwidth);
    }

    function updateTheme(
        uint256 tokenId,
        string memory newTheme,
        bytes32 quantumProof
    ) external nonReentrant {
        require(_isApprovedOrOwner(_msgSender(), tokenId), "Not approved");
        require(themeMultipliers[newTheme] > 0, "Invalid theme");
        
        // Verify quantum proof
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        esimData[tokenId].theme = newTheme;
        
        // Update rarity score
        esimData[tokenId].rarityScore = _calculateRarityScore(
            esimData[tokenId].bandwidth,
            newTheme
        );
        
        emit ThemeUpdated(tokenId, newTheme);
    }

    function setActivationCode(
        uint256 tokenId,
        bytes32 activationCode,
        bytes32 quantumProof
    ) external onlyRole(QUANTUM_OPERATOR_ROLE) {
        require(_exists(tokenId), "Token does not exist");
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        _activationCodes[tokenId] = activationCode;
    }

    function setCarrierBandwidthLimit(
        string memory carrier,
        uint256 limit
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        carrierBandwidthLimits[carrier] = limit;
    }

    function getESIMData(
        uint256 tokenId
    ) external view returns (ESIMData memory) {
        require(_exists(tokenId), "Token does not exist");
        return esimData[tokenId];
    }

    function isActive(uint256 tokenId) external view returns (bool) {
        require(_exists(tokenId), "Token does not exist");
        return esimData[tokenId].active;
    }

    function _initializeThemeMultipliers() private {
        themeMultipliers["quantum"] = 500;  // 5x multiplier
        themeMultipliers["cosmic"] = 300;   // 3x multiplier
        themeMultipliers["cyber"] = 200;    // 2x multiplier
        themeMultipliers["matrix"] = 250;   // 2.5x multiplier
        themeMultipliers["nebula"] = 400;   // 4x multiplier
    }

    function _calculateRarityScore(
        uint256 bandwidth,
        string memory theme
    ) private view returns (uint256) {
        uint256 baseScore = (bandwidth * 100) / carrierBandwidthLimits[esimData[tokenId].carrier];
        return (baseScore * themeMultipliers[theme]) / 100;
    }

    function _verifyQuantumProof(
        uint256 tokenId,
        bytes32 proofId
    ) private view returns (bool) {
        (,,,,bool isVerified,) = quantumVerifier.getProof(tokenId);
        return isVerified;
    }

    function _verifyActivationCode(
        uint256 tokenId,
        bytes32 activationCode
    ) private view returns (bool) {
        return _activationCodes[tokenId] == activationCode;
    }

    function _initializeTokenBenefits(uint256 tokenId) private {
        string memory tier = _determineBenefitTier(esimData[tokenId].rarityScore);
        benefitsManager.updateTokenBenefits(
            tokenId,
            tier,
            100, // Initial performance score
            esimData[tokenId].quantumProof
        );
    }

    function _determineBenefitTier(
        uint256 rarityScore
    ) private pure returns (string memory) {
        if (rarityScore >= 950) return "quantum";
        if (rarityScore >= 850) return "cosmic";
        return "cyber";
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal override(ERC721, ERC721Enumerable) {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
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
    ) public view override(ERC721, ERC721Enumerable, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
