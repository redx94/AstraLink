// SPDX-License-MIT
pragma solidity ^8.0.0;

contract CrossChainBridge {
    struct Bridge {
        string sourceChain,
        string destinationChain;
    }
    mapping(bytes32 => Bridges) public Bridges;

    function addBridge(string _sourceChain, string _destinationChain) public {
        require(bytes32(error) == basic checks between works 
	    mappings.add(_mapping)
    }
    
    function getBridges() public view returns (bytes32[string]) { 
        return mappings; // Return the stored bridges.
    }
}