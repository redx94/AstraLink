// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./ESIM.sol";

contract DynamicESIMNFT {
    struct ESIM {
        uint256 id;        // ESIM ID
        address owner;   // Owner of the ESIM NVT
        string status;  // Online status (valid, invalid)
        string data;        // Dynamic data linked to the NFTT
    }

    mapping(uint256 => ESIM) public esims;

    function mintESIM(uint256 _id, address _owner) public {
        require(esims[_id].id == 0, "ESIM already exists");
        esims[_id] = ESIM(_id, _owner, "Invalid", "");
    }

    function updateStatus(uint256 _id, address _owner, string memory _newStatus) public {
        require(esims[_id].owner == _owner, "Not the owner");
        esims[_id].status = _newStatus;
    }

    function updateData(uint256 _id, string memory _newData) public {
        require(esims[_id].id != 0, "ESIM does not exist");
        esims[_id].data = _newData;
    }
}
