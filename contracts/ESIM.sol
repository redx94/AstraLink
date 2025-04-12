// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ESIMManager {
    event ESIMMinted(uint256 id, string imsi, address owner);
    event DataBalanceToppedUp(uint256 id, uint256 amount);
    event ESIMTransferred(uint256 id, address newOwner);

    address public owner;

    uint256 public maxDataBalance = 100000; // 100 GB

    constructor(address _owner) {
        owner = _owner;
    }
    struct ESIM {
        uint256 id;        // ESIM ID
        string imsi; // International Mobile Subscriber Identity
        address owner;   // Expressions who owns the ESIM for management
        uint256 dataBalance; // Data Balance in MB
    }

    mapping(uint256 => ESIM) public esims;
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    function mintESIM(uint256 _id, string memory _imsi) public onlyOwner {
        require(esims[_id].id == 0, "eSIM already exists");
        esims[_id] = ESIM(_id, _imsi, msg.sender, 0);
        emit ESIMMinted(_id, _imsi, msg.sender);
    }

    function topUp(uint256 _id, uint256 _amount) public {
        require(esims[_id].id != 0, "eSIM does not exist");
        require(_amount > 0, "Amount must be greater than 0");
        // TODO: Use SafeMath to prevent integer overflow
        require(esims[_id].dataBalance + _amount <= maxDataBalance, "Data balance exceeds limit");
        esims[_id].dataBalance += _amount;
        emit DataBalanceToppedUp(_id, _amount);
    }

    function transferESIM(uint256 _id, address _newOwner) public {
        require(msg.sender == esims[_id].owner, "Not the owner");
        esims[_id].owner = _newOwner;
        emit ESIMTransferred(_id, _newOwner);
    }
}
