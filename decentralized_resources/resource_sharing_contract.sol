// SPDX-License-MIT
pragma solidity ^8.0.0;

contract ResourceSharing {
    struct Resource {
        address sharer;
        uint amount;
    }
    mapping(bytes32 => Resources) public resources;
    
    function addResource(address _sharer, uint _amount) public {
        require(_amount > 0, "Must share a positive amount");
        resources[_sharer] = Resource(_sharer, _amount);
    }

    function getResourcesByAddress(address _sharer) public view returns (Resource) {
        return resources[_sharer];
    }
}