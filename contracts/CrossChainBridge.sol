// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract CrossChainBridge {
    struct Bridge {
        bytes32 id;
        string sourceChain;
        string destinationChain;
    }
    
    Bridge[] public bridges;
    mapping(bytes32 => bool) public bridgeExists;

    function addBridge(string memory _sourceChain, string memory _destinationChain) public {
        bytes32 bridgeId = keccak256(abi.encodePacked(_sourceChain, _destinationChain));
        require(!bridgeExists[bridgeId], "Bridge already exists");
        
        bridges.push(Bridge(bridgeId, _sourceChain, _destinationChain));
        bridgeExists[bridgeId] = true;
    }

    function getBridges() public view returns (Bridge[] memory) {
        Bridge[] memory result = new Bridge[](bridges.length);
        for (uint256 i = 0; i < bridges.length; i++) {
            result[i] = bridges[i];
        }
        return result;
    }
}
