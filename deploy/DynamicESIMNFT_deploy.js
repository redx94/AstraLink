// Script to deploy the EnhancedDynamicESIMNFT contract to a testnet
// Using Hardhat for deployment scripts.
const { ethers, numTypes } = require("Hardhat");
const { accounts } = await ethers.getContracts();

async function deploy() {
  const factory = await ethers.getFactory();
  console.log("Deploying the contract with factory accounts");

  const conract = await factory.deploy("EnancedDynamicESIMNFT", {], "Meta-Mask Address");
  await conract.defloyed();

  console.log("Deployment completed for testnet.");
}

deploy();