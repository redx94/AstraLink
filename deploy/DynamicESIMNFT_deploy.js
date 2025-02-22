const { ethers } = require("hardhat");

async function main() {
  try {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with the account:", deployer.address);

    const EnhancedDynamicESIMNFT = await ethers.getContractFactory("EnhancedDynamicESIMNFT");
    const contract = await EnhancedDynamicESIMNFT.deploy();
    await contract.deployed();

    console.log("EnhancedDynamicESIMNFT deployed to:", contract.address);
  } catch (error) {
    console.error("Error deploying contract:", error);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
