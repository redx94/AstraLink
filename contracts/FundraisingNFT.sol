// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract FundraisingNFT is ERC721, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    enum Tier { BASIC, SILVER, GOLD, PLATINUM }

    struct Reward {
        uint256 minContribution;
        string description;
        uint256 vestingPeriod; // in days
    }

    struct Campaign {
        uint256 goal;
        uint256 raised;
        uint256 startTime;
        uint256 endTime;
        bool isActive;
        mapping(Tier => Reward) rewards;
    }

    Campaign public currentCampaign;
    mapping(uint256 => Tier) public tokenTier;
    mapping(uint256 => uint256) public tokenClaimTime;

    event ContributionMade(address contributor, uint256 amount, Tier tier);
    event RewardClaimed(address claimer, uint256 tokenId, Tier tier);

    constructor() ERC721("AstraLinkFundraiser", "ALF") {
        // Initialize default rewards
        currentCampaign.rewards[Tier.BASIC] = Reward(0.1 ether, "Basic supporter NFT", 0);
        currentCampaign.rewards[Tier.SILVER] = Reward(0.5 ether, "Silver supporter NFT with early access", 30);
        currentCampaign.rewards[Tier.GOLD] = Reward(2 ether, "Gold supporter NFT with governance rights", 60);
        currentCampaign.rewards[Tier.PLATINUM] = Reward(5 ether, "Platinum supporter NFT with all benefits", 90);
    }

    function startCampaign(uint256 _goal, uint256 _durationDays) external onlyOwner {
        require(!currentCampaign.isActive, "Campaign already active");
        currentCampaign.goal = _goal;
        currentCampaign.raised = 0;
        currentCampaign.startTime = block.timestamp;
        currentCampaign.endTime = block.timestamp + (_durationDays * 1 days);
        currentCampaign.isActive = true;
    }

    function contribute() external payable {
        require(currentCampaign.isActive, "No active campaign");
        require(block.timestamp < currentCampaign.endTime, "Campaign ended");
        
        currentCampaign.raised += msg.value;
        
        Tier tier = determineTier(msg.value);
        _mintNFT(msg.sender, tier);
        
        emit ContributionMade(msg.sender, msg.value, tier);
    }

    function determineTier(uint256 value) internal view returns (Tier) {
        if (value >= currentCampaign.rewards[Tier.PLATINUM].minContribution) return Tier.PLATINUM;
        if (value >= currentCampaign.rewards[Tier.GOLD].minContribution) return Tier.GOLD;
        if (value >= currentCampaign.rewards[Tier.SILVER].minContribution) return Tier.SILVER;
        return Tier.BASIC;
    }

    function _mintNFT(address to, Tier tier) internal {
        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();
        _safeMint(to, tokenId);
        tokenTier[tokenId] = tier;
        tokenClaimTime[tokenId] = block.timestamp;
    }

    function claimReward(uint256 tokenId) external {
        require(ownerOf(tokenId) == msg.sender, "Not token owner");
        Tier tier = tokenTier[tokenId];
        Reward storage reward = currentCampaign.rewards[tier];
        
        require(block.timestamp >= tokenClaimTime[tokenId] + (reward.vestingPeriod * 1 days), 
            "Vesting period not ended");
        
        emit RewardClaimed(msg.sender, tokenId, tier);
    }

    function withdrawFunds() external onlyOwner {
        require(block.timestamp > currentCampaign.endTime, "Campaign not ended");
        require(currentCampaign.raised >= currentCampaign.goal, "Goal not reached");
        payable(owner()).transfer(address(this).balance);
    }

    function refund() external {
        require(block.timestamp > currentCampaign.endTime, "Campaign not ended");
        require(currentCampaign.raised < currentCampaign.goal, "Goal was reached");
        
        // Implement refund logic here
    }
}