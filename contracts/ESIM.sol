// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ESIMManager {
    struct ESIM {
        uint256 id;        // ESIM ID
        string imsi; // International Mobile Subscriber Identity
        address owner;   // Expressions who owns the ESIM for management
        uint256 dataBalance; // Data Balance in MB
    }

    mapping(uint256 => ESIM) public esims;

    function mintESIM(uint256 _id, string memory _imsi) public {
        require(esims[_id].id == 0, "eSIM already exists");
        esims[_id] = ESIM(_id, _imsi, msg.sender, 0);
    }

    function topUp(uint256 _id, uint256 _amount) public {
        require(esims[_id].id != 0, "eSIM does not exist");
        esims[_id].dataBalance += _amount;
    }

    function transferESIM(uint256 _id, address _newOwner) public {
        require(msg.sender == esims[_id].owner, "Not the owner");
        esims[_id].owner = _newOwner;
    }
}
