const { ethers } = require("hardhat");
const { ESIMNFTService } = require("../blockchain/esim_nft_service");

async function main() {
    const [deployer, user1] = await ethers.getSigners();
    console.log("Deploying and testing Enhanced eSIM NFT system with account:", deployer.address);

    // Deploy QuantumVerifier
    const QuantumVerifier = await ethers.getContractFactory("QuantumVerifier");
    const verifier = await QuantumVerifier.deploy();
    await verifier.waitForDeployment();
    console.log("QuantumVerifier deployed to:", await verifier.getAddress());

    // Deploy EnhancedDynamicESIMNFT
    const ESIMNFT = await ethers.getContractFactory("EnhancedDynamicESIMNFT");
    const esimNFT = await ESIMNFT.deploy();
    await esimNFT.waitForDeployment();
    console.log("EnhancedDynamicESIMNFT deployed to:", await esimNFT.getAddress());

    // Initialize ESIMNFTService
    const nftService = new ESIMNFTService();

    // Demo: Create an eSIM NFT with QR code
    console.log("\nCreating eSIM NFT...");
    
    // Generate quantum signature
    const qSignature = await verifier.generateQuantumChallenge(user1.address);
    
    // Generate activation QR code
    const esimData = {
        carrier: "AstraLink Global",
        activation_code: "LPA:1$astralink.com$1234-5678-90",
        token_id: 1,
        bandwidth: 100
    };
    
    const [qrHash, _] = await nftService.generate_activation_qr(esimData);
    console.log("QR Code generated and uploaded to IPFS:", qrHash);

    // Mint eSIM NFT
    const validityPeriod = 365 * 24 * 60 * 60; // 1 year
    const tx = await esimNFT.mintESIM(
        user1.address,
        1, // tokenId
        100, // bandwidth in Mbps
        qSignature,
        JSON.stringify(esimData),
        validityPeriod,
        qrHash
    );
    await tx.wait();
    console.log("eSIM NFT minted successfully!");

    // Get NFT details
    const details = await esimNFT.getESIMDetails(1);
    console.log("\nNFT Details:");
    console.log("Owner:", details.owner);
    console.log("Bandwidth:", details.bandwidth.toString(), "Mbps");
    console.log("Status:", details.status);
    console.log("Quantum Verified:", details.quantumVerified);

    // Demo marketplace functionality
    console.log("\nTesting marketplace functionality...");
    
    // List eSIM for sale
    const price = ethers.parseEther("0.1"); // 0.1 ETH
    await esimNFT.connect(user1).listESIM(1, price);
    console.log("eSIM listed for sale at", ethers.formatEther(price), "ETH");

    // Check marketplace status
    const esim = await esimNFT.esims(1);
    console.log("Listed:", esim.isListed);
    console.log("Price:", ethers.formatEther(esim.price), "ETH");

    console.log("\nDemo completed successfully!");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });