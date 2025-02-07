// SPDX-License-MIT
pragma solidity ^8.0.0;

contract CrossChainBridge {
    struct Bridge {
        string sourceChain;
        string destinationChain;
    }
    mapping(bytes32 => Bridge) public bridges;

    function addBridge(string memory _sourceChain, string memory _destinationChain) public {
        bytes32 bridgeId = keccak256(abi.encodePacked(_sourceChain, _destinationChain));
        bridges[bridgeId] = Bridge(_sourceChain, _destinationChain);
    }

    function getBridges() public view returns (Bridge[] memory) {
        Bridge[] memory result = new Bridge[](bridges.length);
        uint256 index = 0;
        for (uint256 i = 0; i < bridges.length; i++) {
            if (bridges[i].sourceChain != "") {
                result[index] = bridges[i];
                index++;
            }
        }
        return result;
    }
}
