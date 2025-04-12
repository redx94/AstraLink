const hre = require("hardhat");

async function main() {
  const FundraisingNFT = await hre.ethers.getContractFactory("FundraisingNFT");
  const fundraiser = await FundraisingNFT.deploy();

  await fundraiser.deployed();

  console.log("FundraisingNFT deployed to:", fundraiser.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });