const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("FundraisingNFT", function () {
  let FundraisingNFT;
  let fundraiser;
  let owner;
  let contributor1;
  let contributor2;

  beforeEach(async function () {
    [owner, contributor1, contributor2] = await ethers.getSigners();
    FundraisingNFT = await ethers.getContractFactory("FundraisingNFT");
    fundraiser = await FundraisingNFT.deploy();
  });

  it("Should start a new campaign", async function () {
    await fundraiser.startCampaign(ethers.parseEther("100"), 30);
    const campaign = await fundraiser.currentCampaign();
    expect(campaign.goal).to.equal(ethers.parseEther("100"));
    expect(campaign.isActive).to.be.true;
  });

  it("Should assign correct tiers based on contribution", async function () {
    await fundraiser.startCampaign(ethers.parseEther("100"), 30);
    
    // Basic tier
    await fundraiser.connect(contributor1).contribute({
      value: ethers.parseEther("0.1")
    });
    let tokenId = 0;
    expect(await fundraiser.tokenTier(tokenId)).to.equal(0); // BASIC
    
    // Silver tier
    await fundraiser.connect(contributor2).contribute({
      value: ethers.parseEther("0.5")
    });
    tokenId = 1;
    expect(await fundraiser.tokenTier(tokenId)).to.equal(1); // SILVER
  });

  it("Should allow reward claiming after vesting", async function () {
    await fundraiser.startCampaign(ethers.parseEther("100"), 30);
    await fundraiser.connect(contributor1).contribute({
      value: ethers.parseEther("2") // GOLD tier
    });
    
    // Try to claim immediately (should fail)
    await expect(fundraiser.connect(contributor1).claimReward(0))
      .to.be.revertedWith("Vesting period not ended");
    
    // Fast-forward time by 60 days
    await network.provider.send("evm_increaseTime", [60 * 24 * 60 * 60]);
    await network.provider.send("evm_mine");
    
    // Now claim should succeed
    await expect(fundraiser.connect(contributor1).claimReward(0))
      .to.emit(fundraiser, "RewardClaimed");
  });

  it("Should allow owner to withdraw funds when goal is met", async function () {
    await fundraiser.startCampaign(ethers.parseEther("10"), 30);
    await fundraiser.connect(contributor1).contribute({
      value: ethers.parseEther("10")
    });
    
    // Fast-forward to end of campaign
    await network.provider.send("evm_increaseTime", [30 * 24 * 60 * 60]);
    await network.provider.send("evm_mine");
    
    const ownerBalanceBefore = await ethers.provider.getBalance(owner.address);
    await fundraiser.withdrawFunds();
    const ownerBalanceAfter = await ethers.provider.getBalance(owner.address);
    
    expect(ownerBalanceAfter).to.be.gt(ownerBalanceBefore);
  });
});