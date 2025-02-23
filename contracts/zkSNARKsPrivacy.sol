// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./Verifier.sol"; // Import zk-SNARK verifier contract

/**
 * @title SecureTransactions
 * @dev This contract manages secure transactions using zk-SNARKs for proof verification.
 */
contract SecureTransactions is ReentrancyGuard, Ownable {
    Verifier public verifier;
    
    constructor(address _verifierAddress) {
        verifier = Verifier(_verifierAddress);
    }

    /**
     * @dev Struct to hold transaction details.
     */
    struct Transaction {
        address sender;
        address receiver;
    }

    /**
     * @dev Mapping of proof to transaction struct.
     */
    mapping(bytes32 => Transaction) public transactions;

    /**
     * @dev Function to verify the zk-SNARK proof.
     * @param a The first part of the proof.
     * @param b The second part of the proof.
     * @param c The third part of the proof.
     * @param input The input to the proof.
     * @return True if the proof is valid, false otherwise.
     */
    function verifyProof(
        uint[2] memory a,
        uint[2][2] memory b,
        uint[2] memory c,
        uint[2] memory input
    ) public view returns (bool) {
        return verifier.verifyProof(a, b, c, input);
    }

    /**
     * @dev Function to transfer funds with proof verification.
     * @param _sender The sender address.
     * @param _receiver The receiver address.
     * @param a The first part of the proof.
     * @param b The second part of the proof.
     * @param c The third part of the proof.
     * @param input The input to the proof.
     */
    function transfer(
        address _sender,
        address _receiver,
        uint[2] memory a,
        uint[2][2] memory b,
        uint[2] memory c,
        uint[2] memory input
    ) public nonReentrant onlyOwner {
        require(verifyProof(a, b, c, input), "Invalid zk-SNARK proof");
        transactions[keccak256(abi.encodePacked(a, b, c, input))] = 
            Transaction(_sender, _receiver);
    }
}
