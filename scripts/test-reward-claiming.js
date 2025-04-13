const hre = require("hardhat");

async function main() {
  const contractAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
  const FundraisingNFT = await hre.ethers.getContractFactory("FundraisingNFT");
  const fundraiser = FundraisingNFT.attach(contractAddress);

  // Get the contributor's address (account[1] from previous contribution)
  const [_, contributor] = await hre.ethers.getSigners();
  console.log("Checking NFT status for contributor:", contributor.address);

  // Get contributor's NFT balance
  const balance = await fundraiser.balanceOf(contributor.address);
  console.log(`NFT Balance: ${balance.toString()}`);

  // The contributor should have token ID 0 from their contribution
  const tokenId = 0;
  const tier = await fundraiser.tokenTier(tokenId);
  console.log(`NFT Tier: ${['BASIC', 'SILVER', 'GOLD', 'PLATINUM'][tier]}`);

  // Try to claim reward before vesting period (should fail)
  console.log("\nTrying to claim reward before vesting period...");
  try {
    await fundraiser.connect(contributor).claimReward(tokenId);
  } catch (error) {
    console.log("Failed as expected:", error.message);
  }

  // Fast forward time by 60 days (GOLD tier vesting period)
  console.log("\nFast forwarding time by 60 days...");
  await hre.network.provider.send("evm_increaseTime", [60 * 24 * 60 * 60]);
  await hre.network.provider.send("evm_mine");

  // Try to claim reward after vesting period (should succeed)
  console.log("\nTrying to claim reward after vesting period...");
  const claimTx = await fundraiser.connect(contributor).claimReward(tokenId);
  await claimTx.wait();
  console.log("Successfully claimed reward!");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});