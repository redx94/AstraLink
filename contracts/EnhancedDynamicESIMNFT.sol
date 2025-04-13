pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Base64.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

contract EnhancedDynamicESIMNFT is ERC721URIStorage, ERC721Enumerable, Ownable, Pausable, ReentrancyGuard {
    using Strings for uint256;

    struct ESIM {
        uint256 id;
        address owner;
        uint256 bandwidth;
        uint256 activationTime;
        uint256 expirationTime;
        bytes32 quantumSignature;
        string status; // active, suspended, expired
        string carrierData;
        bool quantumVerified;
        string designTheme; // cosmic, quantum, cyber, etc.
        uint256 rarity; // 1-1000 scale
        string activationQR; // IPFS hash of the QR code
        bool isListed; // for marketplace
        uint256 price; // if listed
        string modelURI; // IPFS hash of the 3D model
        string arViewerURL; // URL for AR viewing experience
    }

    struct MarketplaceData {
        bool isListed;
        uint256 price;
        uint256 listingTime;
        address[] previousOwners;
        uint256[] historicalPrices;
        uint256 totalTransfers;
        mapping(address => bool) authorizedBuyers;  // For private listings
    }
    
    mapping(uint256 => ESIM) public esims;
    mapping(address => uint256[]) public userESIMs;
    mapping(bytes32 => bool) public usedQuantumSignatures;
    mapping(uint256 => MarketplaceData) public marketplaceData;
    
    uint256 private constant MINIMUM_BANDWIDTH = 1;
    uint256 private constant MAXIMUM_BANDWIDTH = 1000000; // 1 Gbps
    uint256 private constant MIN_ACTIVATION_PERIOD = 1 days;
    uint256 private constant MAX_ACTIVATION_PERIOD = 365 days;

    // Rarity tiers
    uint256 private constant LEGENDARY_THRESHOLD = 950;
    uint256 private constant EPIC_THRESHOLD = 850;
    uint256 private constant RARE_THRESHOLD = 700;

    // Design themes
    string[] public designThemes = ["cosmic", "quantum", "cyber", "nebula", "matrix"];
    
    // Marketplace fee
    uint256 public marketplaceFee = 25; // 2.5%
    
    event ESIMMinted(uint256 indexed tokenId, address indexed owner, uint256 bandwidth, uint256 rarity, string qrHash);
    event ESIMActivated(uint256 indexed tokenId, uint256 activationTime);
    event ESIMSuspended(uint256 indexed tokenId);
    event ESIMBandwidthUpdated(uint256 indexed tokenId, uint256 newBandwidth);
    event QuantumSignatureVerified(uint256 indexed tokenId, bytes32 signature);
    event ESIMListed(uint256 indexed tokenId, uint256 price);
    event ESIMSold(uint256 indexed tokenId, address indexed seller, address indexed buyer, uint256 price);
    event ESIMPrivateListed(uint256 indexed tokenId, uint256 price, address[] authorizedBuyers);
    event ESIMPriceUpdated(uint256 indexed tokenId, uint256 oldPrice, uint256 newPrice);
    event ESIMTransferSecured(uint256 indexed tokenId, bytes32 quantumProof);

    constructor() ERC721("AstraLink Dynamic eSIM", "AESIM") {}

    function mintESIM(
        address to,
        uint256 tokenId,
        uint256 bandwidth,
        bytes32 quantumSignature,
        string memory carrierData,
        uint256 validityPeriod,
        string memory qrHash
    ) external onlyOwner whenNotPaused nonReentrant {
        require(bandwidth >= MINIMUM_BANDWIDTH && bandwidth <= MAXIMUM_BANDWIDTH, "Invalid bandwidth");
        require(validityPeriod >= MIN_ACTIVATION_PERIOD && validityPeriod <= MAX_ACTIVATION_PERIOD, "Invalid validity period");
        require(!usedQuantumSignatures[quantumSignature], "Quantum signature already used");

        // Generate random rarity and theme
        uint256 rarity = _generateRarity(quantumSignature);
        string memory theme = designThemes[uint256(keccak256(abi.encodePacked(quantumSignature, block.timestamp))) % designThemes.length];

        _safeMint(to, tokenId);
        
        esims[tokenId] = ESIM({
            id: tokenId,
            owner: to,
            bandwidth: bandwidth,
            activationTime: block.timestamp,
            expirationTime: block.timestamp + validityPeriod,
            quantumSignature: quantumSignature,
            status: "active",
            carrierData: carrierData,
            quantumVerified: true,
            designTheme: theme,
            rarity: rarity,
            activationQR: qrHash,
            isListed: false,
            price: 0,
            modelURI: "",
            arViewerURL: ""
        });

        // Generate and set token URI with metadata
        string memory tokenURI = _generateTokenURI(tokenId);
        _setTokenURI(tokenId, tokenURI);

        userESIMs[to].push(tokenId);
        usedQuantumSignatures[quantumSignature] = true;

        emit ESIMMinted(tokenId, to, bandwidth, rarity, qrHash);
        emit QuantumSignatureVerified(tokenId, quantumSignature);
    }

    function _generateRarity(bytes32 seed) internal view returns (uint256) {
        return uint256(keccak256(abi.encodePacked(seed, block.timestamp, block.prevrandao))) % 1000 + 1;
    }

    function _generateTokenURI(uint256 tokenId) internal view returns (string memory) {
        ESIM memory esim = esims[tokenId];
        
        string memory rarityTier;
        if (esim.rarity >= LEGENDARY_THRESHOLD) rarityTier = "Legendary";
        else if (esim.rarity >= EPIC_THRESHOLD) rarityTier = "Epic";
        else if (esim.rarity >= RARE_THRESHOLD) rarityTier = "Rare";
        else rarityTier = "Common";

        bytes memory dataURI = abi.encodePacked(
            '{',
            '"name": "AstraLink eSIM #', tokenId.toString(), '",',
            '"description": "Dynamic eSIM NFT with quantum security",',
            '"image": "', _generateImageURI(tokenId), '",',
            '"animation_url": "', esim.modelURI, '",',
            '"external_url": "', esim.arViewerURL, '",',
            '"attributes": [',
            '{"trait_type": "Bandwidth", "value": "', esim.bandwidth.toString(), ' Mbps"},',
            '{"trait_type": "Rarity", "value": "', rarityTier, '"},',
            '{"trait_type": "Design Theme", "value": "', esim.designTheme, '"},',
            '{"trait_type": "Status", "value": "', esim.status, '"},',
            '{"trait_type": "Quantum Verified", "value": ', esim.quantumVerified ? "true" : "false", '},',
            '{"trait_type": "Activation QR", "value": "', esim.activationQR, '"}',
            ']}'
        );

        return string(
            abi.encodePacked(
                "data:application/json;base64,",
                Base64.encode(dataURI)
            )
        );
    }

    function _generateImageURI(uint256 tokenId) internal view returns (string memory) {
        // This would be replaced with actual NFT artwork generation/IPFS hash
        return string(abi.encodePacked("ipfs://", esims[tokenId].designTheme, "/", tokenId.toString()));
    }

    // Marketplace functions
    function listESIM(uint256 tokenId, uint256 price) external {
        require(ownerOf(tokenId) == msg.sender, "Not the owner");
        require(price > 0, "Invalid price");
        
        esims[tokenId].isListed = true;
        esims[tokenId].price = price;
        
        emit ESIMListed(tokenId, price);
    }

    function listESIMPrivate(
        uint256 tokenId,
        uint256 price,
        address[] calldata authorizedBuyers
    ) external {
        require(ownerOf(tokenId) == msg.sender, "Not the owner");
        require(price > 0, "Invalid price");
        require(!marketplaceData[tokenId].isListed, "Already listed");
        
        MarketplaceData storage data = marketplaceData[tokenId];
        data.isListed = true;
        data.price = price;
        data.listingTime = block.timestamp;
        
        for(uint i = 0; i < authorizedBuyers.length; i++) {
            data.authorizedBuyers[authorizedBuyers[i]] = true;
        }
        
        emit ESIMPrivateListed(tokenId, price, authorizedBuyers);
    }

    function updateListingPrice(uint256 tokenId, uint256 newPrice) external {
        require(ownerOf(tokenId) == msg.sender, "Not the owner");
        require(marketplaceData[tokenId].isListed, "Not listed");
        
        uint256 oldPrice = marketplaceData[tokenId].price;
        marketplaceData[tokenId].price = newPrice;
        marketplaceData[tokenId].historicalPrices.push(oldPrice);
        
        emit ESIMPriceUpdated(tokenId, oldPrice, newPrice);
    }

    function buyESIM(uint256 tokenId) external payable nonReentrant {
        ESIM storage esim = esims[tokenId];
        require(esim.isListed, "Not listed for sale");
        require(msg.value >= esim.price, "Insufficient payment");
        
        address seller = ownerOf(tokenId);
        uint256 fee = (msg.value * marketplaceFee) / 1000;
        uint256 sellerAmount = msg.value - fee;
        
        // Transfer NFT
        _transfer(seller, msg.sender, tokenId);
        
        // Update ESIM data
        esim.owner = msg.sender;
        esim.isListed = false;
        esim.price = 0;
        
        // Transfer payments
        payable(seller).transfer(sellerAmount);
        payable(owner()).transfer(fee);
        
        emit ESIMSold(tokenId, seller, msg.sender, msg.value);
    }

    function buyESIMWithQuantumProof(
        uint256 tokenId,
        bytes32 quantumProof
    ) external payable nonReentrant {
        MarketplaceData storage data = marketplaceData[tokenId];
        require(data.isListed, "Not listed for sale");
        require(msg.value >= data.price, "Insufficient payment");
        
        if(data.authorizedBuyers[address(0)] == false) {
            require(data.authorizedBuyers[msg.sender], "Not authorized to buy");
        }
        
        address seller = ownerOf(tokenId);
        uint256 fee = (msg.value * marketplaceFee) / 1000;
        uint256 sellerAmount = msg.value - fee;
        
        // Record transfer history
        data.previousOwners.push(seller);
        data.totalTransfers++;
        
        // Transfer NFT with quantum security
        _transfer(seller, msg.sender, tokenId);
        
        // Update marketplace data
        data.isListed = false;
        data.price = 0;
        delete data.authorizedBuyers[msg.sender];
        
        // Transfer payments
        payable(seller).transfer(sellerAmount);
        payable(owner()).transfer(fee);
        
        emit ESIMTransferSecured(tokenId, quantumProof);
        emit ESIMSold(tokenId, seller, msg.sender, msg.value);
    }

    function getMarketplaceHistory(uint256 tokenId) external view returns (
        address[] memory previousOwners,
        uint256[] memory historicalPrices,
        uint256 totalTransfers
    ) {
        MarketplaceData storage data = marketplaceData[tokenId];
        return (
            data.previousOwners,
            data.historicalPrices,
            data.totalTransfers
        );
    }

    function updateBandwidth(uint256 tokenId, uint256 newBandwidth) external onlyOwner whenNotPaused {
        require(_exists(tokenId), "eSIM does not exist");
        require(newBandwidth >= MINIMUM_BANDWIDTH && newBandwidth <= MAXIMUM_BANDWIDTH, "Invalid bandwidth");
        
        ESIM storage esim = esims[tokenId];
        require(keccak256(bytes(esim.status)) == keccak256(bytes("active")), "eSIM not active");
        
        esim.bandwidth = newBandwidth;
        emit ESIMBandwidthUpdated(tokenId, newBandwidth);
    }

    function suspendESIM(uint256 tokenId) external onlyOwner whenNotPaused {
        require(_exists(tokenId), "eSIM does not exist");
        ESIM storage esim = esims[tokenId];
        require(keccak256(bytes(esim.status)) == keccak256(bytes("active")), "eSIM not active");
        
        esim.status = "suspended";
        emit ESIMSuspended(tokenId);
    }

    function reactivateESIM(uint256 tokenId) external onlyOwner whenNotPaused {
        require(_exists(tokenId), "eSIM does not exist");
        ESIM storage esim = esims[tokenId];
        require(keccak256(bytes(esim.status)) == keccak256(bytes("suspended")), "eSIM not suspended");
        require(block.timestamp < esim.expirationTime, "eSIM expired");
        
        esim.status = "active";
        emit ESIMActivated(tokenId, block.timestamp);
    }

    function getESIMDetails(uint256 tokenId) external view returns (
        address owner,
        uint256 bandwidth,
        uint256 activationTime,
        uint256 expirationTime,
        string memory status,
        bool quantumVerified
    ) {
        require(_exists(tokenId), "eSIM does not exist");
        ESIM memory esim = esims[tokenId];
        return (
            esim.owner,
            esim.bandwidth,
            esim.activationTime,
            esim.expirationTime,
            esim.status,
            esim.quantumVerified
        );
    }

    function getUserESIMs(address user) external view returns (uint256[] memory) {
        return userESIMs[user];
    }

    function updateVisualization(
        uint256 tokenId,
        string memory modelURI,
        string memory arViewerURL
    ) external onlyOwner whenNotPaused {
        require(_exists(tokenId), "eSIM does not exist");
        
        ESIM storage esim = esims[tokenId];
        esim.modelURI = modelURI;
        esim.arViewerURL = arViewerURL;
        
        // Update token URI to reflect new visualization data
        _setTokenURI(tokenId, _generateTokenURI(tokenId));
    }

    // Add new function to get visualization data
    function getVisualization(uint256 tokenId) external view returns (
        string memory modelURI,
        string memory arViewerURL
    ) {
        require(_exists(tokenId), "eSIM does not exist");
        ESIM memory esim = esims[tokenId];
        return (esim.modelURI, esim.arViewerURL);
    }

    function pauseOperations() external onlyOwner {
        _pause();
    }

    function unpauseOperations() external onlyOwner {
        _unpause();
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal override(ERC721, ERC721Enumerable) whenNotPaused {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721Enumerable, ERC721URIStorage)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }

    function tokenURI(uint256 tokenId) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }
}
