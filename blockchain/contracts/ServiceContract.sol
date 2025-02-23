// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract AstraLinkService is Ownable {
    struct Provider {
        address payable wallet;
        uint256 commissionRate; // Base points (1% = 100)
        bool isActive;
        uint256 totalEarnings;
    }

    struct ServicePlan {
        uint256 price;
        uint256 duration;
        uint256 dataLimit;
        string serviceType; // "5G", "6G", "Satellite"
        bool isActive;
    }

    mapping(address => Provider) public providers;
    mapping(uint256 => ServicePlan) public servicePlans;
    mapping(address => mapping(uint256 => uint256)) public userSubscriptions; // user => planId => expiry

    uint256 public platformFee = 1500; // 15% in base points
    address payable public techOwnerWallet;
    uint256 public totalRevenue;

    event ProviderAdded(address provider, uint256 commissionRate);
    event ServiceActivated(address user, uint256 planId, uint256 expiry);
    event RevenueDistributed(address provider, uint256 amount, uint256 platformFee);

    constructor(address payable _techOwnerWallet) {
        techOwnerWallet = _techOwnerWallet;
    }

    function addProvider(
        address payable _provider,
        uint256 _commissionRate
    ) external onlyOwner {
        require(_commissionRate <= 8000, "Commission too high"); // Max 80%
        providers[_provider] = Provider({
            wallet: _provider,
            commissionRate: _commissionRate,
            isActive: true,
            totalEarnings: 0
        });
        emit ProviderAdded(_provider, _commissionRate);
    }

    function addServicePlan(
        uint256 _planId,
        uint256 _price,
        uint256 _duration,
        uint256 _dataLimit,
        string memory _serviceType
    ) external onlyOwner {
        servicePlans[_planId] = ServicePlan({
            price: _price,
            duration: _duration,
            dataLimit: _dataLimit,
            serviceType: _serviceType,
            isActive: true
        });
    }

    function activateService(uint256 _planId) external payable {
        ServicePlan memory plan = servicePlans[_planId];
        require(plan.isActive, "Plan not active");
        require(msg.value >= plan.price, "Insufficient payment");

        // Calculate revenue distribution
        uint256 platformAmount = (msg.value * platformFee) / 10000;
        uint256 providerAmount = msg.value - platformAmount;

        // Transfer platform fee to tech owner
        techOwnerWallet.transfer(platformAmount);

        // Update provider earnings
        Provider storage provider = providers[msg.sender];
        provider.totalEarnings += providerAmount;

        // Activate subscription
        uint256 expiry = block.timestamp + plan.duration;
        userSubscriptions[msg.sender][_planId] = expiry;

        emit ServiceActivated(msg.sender, _planId, expiry);
        emit RevenueDistributed(msg.sender, providerAmount, platformAmount);
    }

    function updatePlatformFee(uint256 _newFee) external onlyOwner {
        require(_newFee <= 3000, "Fee too high"); // Max 30%
        platformFee = _newFee;
    }

    function withdrawProviderEarnings() external {
        Provider storage provider = providers[msg.sender];
        require(provider.isActive, "Provider not active");
        require(provider.totalEarnings > 0, "No earnings to withdraw");

        uint256 amount = provider.totalEarnings;
        provider.totalEarnings = 0;
        provider.wallet.transfer(amount);
    }
}
