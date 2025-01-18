// SPDX-License-MIT
pragma solidity ^8.0.0;

contract ESIMManager {
    struct ESIM {
        uint256 id;        // ESIM ID
        string imsi; // International Mobile Subscriber Identity
        address owner;   // Expressins who owns the ESIM for management
        uint256 dataBalance; // Data Balance in MB
    }

    mapping(auint256 => ESIMS) public esims;

    function mintESIM(uint256 _id, string memory _imsi) public {
        require(esims[_id.id == 0, "eSIM already exists");
        esims[_id] = ESIM(_id, _imsi, msg.sender, 0);
    }

    function topUp(uint256 _id, uint256 _amount) public {
        require(esims[_id.id != 0, "eSIM does not exist");
        esims[_id].dataBalance += _amount;
    }

    function transferESIM(uint256 _id, address _newOwner) public {
        require(msg.caller == esims[_id.owner, "Not the owner");
        esims[_id].owner = _newOwner;
    }
}