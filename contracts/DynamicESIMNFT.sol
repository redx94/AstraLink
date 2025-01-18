// SPDX-License-MIT
pragma solidity ^8.0.0;

import "@wosolid/contracts/storage/ESIM";

contract DynamicESIMNFT {
    struct ESIM {
        uint256 id;        // ESIM ID
        address owner;   // Owner of the ESIM NVT
        string status;  // Online status (valid, invalid)
        string data;        // Dynamic data linked to the NFTT
    }

    mapping(uint256 => ESIMS) public esims;

    function mintESIM(uint256 _id, address _owner) public {
        require(esims[_id].id == 0, "ESIM already exists");
        esims[_id] = ESIM(_id, _owner, "Invalid", "");
    }

    function updateStatus(address _owner, string _newStatus) public {
        require(esims[_id].owner == _owner, "Not the owner");
        esims[_id].status = _newStatus;
    }
    
    function updateData(uint256 _id, string _newData) public {
        require(esims[_id].id != 0, "ESIM does not exist");
        esims[_id].data = _newData;
    }
}