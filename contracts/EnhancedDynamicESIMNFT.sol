// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract EnhancedDynamicESIMNFT is ERC721, Ownable, ReentrancyGuard {
    struct ESIM {
        uint256 id;
        address owner;
        string status;
        string metadata;
    }

    mapping(uint256 => ESIM) private esims;

    constructor() ERC721("DynamicESIMNFT", "DESIM") { }

    function mintESIM(uint256 _id, address _to, string memory metadata) external onlyOwner nonReentrant {
        require(_id != 0, "ID must be non-zero");
        require(_to != address(0), "Invalid address");
        require(esims[_id].id == 0, "ESIM already exists");
        _safeMint(_to, _id);
        esims[_id] = ESIM(_id, _to, "Valid", metadata);
    }

    function updateStatus(uint256 _id, string memory _newStatus) external nonReentrant {
        require(ownerOf(_id) == msg.sender, "Only the owner can update status");
        esims[_id].status = _newStatus;
    }

    function updateMetadata(uint256 _id, string memory _newMetadata) external nonReentrant {
        require(ownerOf(_id) == msg.sender, "Only the owner can update metadata");
        esims[_id].metadata = _newMetadata;
    }

    function getESIM(uint256 _id) external view returns (ESIM memory) {
        return esims[_id];
    }
}
