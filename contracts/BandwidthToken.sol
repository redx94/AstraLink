// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "./QuantumVerifier.sol";

/**
 * @title BandwidthToken
 * @dev ERC20 token representing bandwidth allocation with quantum security
 */
contract BandwidthToken is ERC20, ERC20Burnable, ReentrancyGuard, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant BANDWIDTH_OPERATOR_ROLE = keccak256("BANDWIDTH_OPERATOR_ROLE");

    // Reference to QuantumVerifier contract
    QuantumVerifier public quantumVerifier;

    struct BandwidthAllocation {
        uint256 amount;
        uint256 startTime;
        uint256 endTime;
        bytes32 quantumProof;
        bool active;
    }

    // Mapping from token ID to bandwidth allocation
    mapping(uint256 => BandwidthAllocation) public allocations;
    
    // Mapping for bandwidth usage tracking
    mapping(uint256 => uint256) public bandwidthUsed;
    
    // Rate limiting parameters
    uint256 public constant RATE_LIMIT_WINDOW = 3600; // 1 hour
    mapping(uint256 => mapping(uint256 => uint256)) public hourlyUsage;

    event BandwidthAllocated(
        uint256 indexed tokenId,
        uint256 amount,
        uint256 startTime,
        uint256 endTime
    );
    event BandwidthConsumed(uint256 indexed tokenId, uint256 amount);
    event AllocationActivated(uint256 indexed tokenId, bytes32 quantumProof);
    event AllocationDeactivated(uint256 indexed tokenId);
    event RateLimitUpdated(uint256 indexed tokenId, uint256 newLimit);

    constructor(
        address _quantumVerifier
    ) ERC20("BandwidthToken", "BAND") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        quantumVerifier = QuantumVerifier(_quantumVerifier);
    }

    function allocateBandwidth(
        uint256 tokenId,
        uint256 amount,
        uint256 duration,
        bytes32 quantumProof
    ) external onlyRole(BANDWIDTH_OPERATOR_ROLE) nonReentrant {
        require(amount > 0, "Amount must be positive");
        require(duration > 0, "Duration must be positive");
        require(
            allocations[tokenId].endTime < block.timestamp,
            "Existing allocation active"
        );
        
        // Verify quantum proof
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        // Create allocation
        allocations[tokenId] = BandwidthAllocation({
            amount: amount,
            startTime: block.timestamp,
            endTime: block.timestamp + duration,
            quantumProof: quantumProof,
            active: true
        });
        
        // Mint tokens
        _mint(msg.sender, amount);
        
        emit BandwidthAllocated(
            tokenId,
            amount,
            block.timestamp,
            block.timestamp + duration
        );
    }

    function consumeBandwidth(
        uint256 tokenId,
        uint256 amount,
        bytes32 quantumProof
    ) external onlyRole(BANDWIDTH_OPERATOR_ROLE) nonReentrant {
        require(
            allocations[tokenId].active,
            "Allocation not active"
        );
        require(
            block.timestamp <= allocations[tokenId].endTime,
            "Allocation expired"
        );
        require(
            bandwidthUsed[tokenId] + amount <= allocations[tokenId].amount,
            "Exceeds allocation"
        );
        
        // Verify quantum proof
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        // Check rate limit
        require(
            _checkRateLimit(tokenId, amount),
            "Rate limit exceeded"
        );
        
        // Update usage
        bandwidthUsed[tokenId] += amount;
        _updateHourlyUsage(tokenId, amount);
        
        // Burn tokens
        _burn(msg.sender, amount);
        
        emit BandwidthConsumed(tokenId, amount);
    }

    function activateAllocation(
        uint256 tokenId,
        bytes32 quantumProof
    ) external onlyRole(BANDWIDTH_OPERATOR_ROLE) nonReentrant {
        require(
            !allocations[tokenId].active,
            "Already active"
        );
        require(
            block.timestamp <= allocations[tokenId].endTime,
            "Allocation expired"
        );
        
        // Verify quantum proof
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        allocations[tokenId].active = true;
        allocations[tokenId].quantumProof = quantumProof;
        
        emit AllocationActivated(tokenId, quantumProof);
    }

    function deactivateAllocation(
        uint256 tokenId,
        bytes32 quantumProof
    ) external onlyRole(BANDWIDTH_OPERATOR_ROLE) nonReentrant {
        require(
            allocations[tokenId].active,
            "Not active"
        );
        
        // Verify quantum proof
        require(
            _verifyQuantumProof(tokenId, quantumProof),
            "Invalid quantum proof"
        );
        
        allocations[tokenId].active = false;
        
        emit AllocationDeactivated(tokenId);
    }

    function getBandwidthUsage(
        uint256 tokenId
    ) external view returns (
        uint256 used,
        uint256 remaining,
        uint256 hourlyRate
    ) {
        BandwidthAllocation memory allocation = allocations[tokenId];
        uint256 currentHour = block.timestamp / RATE_LIMIT_WINDOW;
        
        return (
            bandwidthUsed[tokenId],
            allocation.amount - bandwidthUsed[tokenId],
            hourlyUsage[tokenId][currentHour]
        );
    }

    function _verifyQuantumProof(
        uint256 tokenId,
        bytes32 proofId
    ) private view returns (bool) {
        (,,,,bool isVerified,) = quantumVerifier.getProof(tokenId);
        return isVerified;
    }

    function _checkRateLimit(
        uint256 tokenId,
        uint256 amount
    ) private view returns (bool) {
        uint256 currentHour = block.timestamp / RATE_LIMIT_WINDOW;
        uint256 currentUsage = hourlyUsage[tokenId][currentHour];
        uint256 hourlyLimit = allocations[tokenId].amount / 24; // Daily allocation divided by 24
        
        return currentUsage + amount <= hourlyLimit;
    }

    function _updateHourlyUsage(
        uint256 tokenId,
        uint256 amount
    ) private {
        uint256 currentHour = block.timestamp / RATE_LIMIT_WINDOW;
        hourlyUsage[tokenId][currentHour] += amount;
    }
}
