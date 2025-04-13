const hre = require("hardhat");

async function main() {
  const contractAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
  const FundraisingNFT = await hre.ethers.getContractFactory("FundraisingNFT");
  const fundraiser = FundraisingNFT.attach(contractAddress);

  // Get signers (accounts)
  const [owner, contributor1] = await hre.ethers.getSigners();
  
  console.log("Making a contribution from:", contributor1.address);
  
  // Contribute 2 ETH (GOLD tier)
  const contributionAmount = hre.ethers.parseEther("2");
  
  // Make contribution
  const tx = await fundraiser.connect(contributor1).contribute({ value: contributionAmount });
  await tx.wait();
  
  console.log(`Successfully contributed ${hre.ethers.formatEther(contributionAmount)} ETH!`);
  
  // Get campaign status
  const campaign = await fundraiser.currentCampaign();
  console.log(`\nCampaign Status:`);
  console.log(`Goal: ${hre.ethers.formatEther(campaign.goal)} ETH`);
  console.log(`Raised so far: ${hre.ethers.formatEther(campaign.raised)} ETH`);
  console.log(`Progress: ${(Number(campaign.raised) * 100 / Number(campaign.goal)).toFixed(2)}%`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});