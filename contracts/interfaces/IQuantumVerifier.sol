// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IQuantumVerifier {
    function verifyQuantumSignature(bytes32 signature, bytes memory data) external view returns (bool);
    function generateQuantumChallenge(address user) external view returns (bytes32);
    function validateEntanglement(bytes32 signature, bytes32 challenge) external view returns (bool);
}