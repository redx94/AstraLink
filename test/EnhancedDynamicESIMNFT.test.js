const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("EnhancedDynamicESIMNFT", function () {
  let ESIMContract;
  let QuantumVerifier;
  let esimNFT;
  let quantumVerifier;
  let owner;
  let user1;
  let user2;

  beforeEach(async function () {
    [owner, user1, user2] = await ethers.getSigners();

    // Deploy QuantumVerifier
    QuantumVerifier = await ethers.getContractFactory("QuantumVerifier");
    quantumVerifier = await QuantumVerifier.deploy();
    await quantumVerifier.waitForDeployment();

    // Deploy EnhancedDynamicESIMNFT
    ESIMContract = await ethers.getContractFactory("EnhancedDynamicESIMNFT");
    esimNFT = await ESIMContract.deploy();
    await esimNFT.waitForDeployment();
  });

  describe("eSIM Minting", function () {
    it("Should mint an eSIM with quantum verification", async function () {
      const tokenId = 1;
      const bandwidth = 100; // 100 Mbps
      const validityPeriod = 30 * 24 * 60 * 60; // 30 days
      
      // Generate quantum signature
      const data = ethers.solidityPacked(
        ["address", "uint256", "uint256"],
        [user1.address, tokenId, bandwidth]
      );
      const quantumSignature = await quantumVerifier.generateQuantumChallenge(user1.address);
      
      // Mint eSIM
      await expect(esimNFT.mintESIM(
        user1.address,
        tokenId,
        bandwidth,
        quantumSignature,
        "carrier-data-hash",
        validityPeriod
      )).to.emit(esimNFT, "ESIMMinted")
        .withArgs(tokenId, user1.address, bandwidth);

      // Verify eSIM details
      const esimDetails = await esimNFT.getESIMDetails(tokenId);
      expect(esimDetails.owner).to.equal(user1.address);
      expect(esimDetails.bandwidth).to.equal(bandwidth);
      expect(esimDetails.status).to.equal("active");
      expect(esimDetails.quantumVerified).to.be.true;
    });

    it("Should properly track user's eSIMs", async function () {
      // Mint multiple eSIMs for user1
      const bandwidth = 100;
      const validityPeriod = 30 * 24 * 60 * 60;
      
      for (let i = 1; i <= 3; i++) {
        const quantumSignature = await quantumVerifier.generateQuantumChallenge(user1.address);
        await esimNFT.mintESIM(
          user1.address,
          i,
          bandwidth,
          quantumSignature,
          "carrier-data-hash",
          validityPeriod
        );
      }

      const userESIMs = await esimNFT.getUserESIMs(user1.address);
      expect(userESIMs.length).to.equal(3);
      expect(userESIMs[0]).to.equal(1);
      expect(userESIMs[1]).to.equal(2);
      expect(userESIMs[2]).to.equal(3);
    });
  });

  describe("eSIM Management", function () {
    let tokenId;
    let quantumSignature;

    beforeEach(async function () {
      tokenId = 1;
      quantumSignature = await quantumVerifier.generateQuantumChallenge(user1.address);
      
      await esimNFT.mintESIM(
        user1.address,
        tokenId,
        100,
        quantumSignature,
        "carrier-data-hash",
        30 * 24 * 60 * 60
      );
    });

    it("Should update bandwidth correctly", async function () {
      const newBandwidth = 200;
      await esimNFT.updateBandwidth(tokenId, newBandwidth);
      
      const esimDetails = await esimNFT.getESIMDetails(tokenId);
      expect(esimDetails.bandwidth).to.equal(newBandwidth);
    });

    it("Should suspend and reactivate eSIM", async function () {
      // Suspend eSIM
      await esimNFT.suspendESIM(tokenId);
      let esimDetails = await esimNFT.getESIMDetails(tokenId);
      expect(esimDetails.status).to.equal("suspended");

      // Reactivate eSIM
      await esimNFT.reactivateESIM(tokenId);
      esimDetails = await esimNFT.getESIMDetails(tokenId);
      expect(esimDetails.status).to.equal("active");
    });
  });

  describe("Security Features", function () {
    it("Should prevent reuse of quantum signatures", async function () {
      const tokenId1 = 1;
      const tokenId2 = 2;
      const quantumSignature = await quantumVerifier.generateQuantumChallenge(user1.address);

      await esimNFT.mintESIM(
        user1.address,
        tokenId1,
        100,
        quantumSignature,
        "carrier-data-hash",
        30 * 24 * 60 * 60
      );

      await expect(esimNFT.mintESIM(
        user1.address,
        tokenId2,
        100,
        quantumSignature,
        "carrier-data-hash",
        30 * 24 * 60 * 60
      )).to.be.revertedWith("Quantum signature already used");
    });

    it("Should enforce bandwidth limits", async function () {
      const tokenId = 1;
      const quantumSignature = await quantumVerifier.generateQuantumChallenge(user1.address);
      
      // Try to mint with too high bandwidth
      await expect(esimNFT.mintESIM(
        user1.address,
        tokenId,
        1000001, // Above MAXIMUM_BANDWIDTH
        quantumSignature,
        "carrier-data-hash",
        30 * 24 * 60 * 60
      )).to.be.revertedWith("Invalid bandwidth");
    });
  });
});