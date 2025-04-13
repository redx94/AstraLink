const hre = require("hardhat");

async function main() {
  console.log("Deploying FundraisingNFT...");
  
  const FundraisingNFT = await hre.ethers.getContractFactory("FundraisingNFT");
  const fundraiser = await FundraisingNFT.deploy();
  await fundraiser.waitForDeployment();
  
  const address = await fundraiser.getAddress();
  console.log(`FundraisingNFT deployed to: ${address}`);

  // Start a campaign
  // Goal: 10 ETH
  // Duration: 30 days
  console.log("Starting fundraising campaign...");
  const goal = hre.ethers.parseEther("10");
  await fundraiser.startCampaign(goal, 30);
  console.log("Campaign started!");

  // Log the tiers and minimum contributions
  console.log("\nContribution tiers:");
  console.log("- BASIC: 0.1 ETH");
  console.log("- SILVER: 0.5 ETH");
  console.log("- GOLD: 2 ETH");
  console.log("- PLATINUM: 5 ETH");

  console.log("\nContract is ready to accept contributions!");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});