// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title EnhancedDynamicESIMNFT
 * @dev This contract extends ERC721 to manage Enhanced Dynamic ESIM NFTs with additional functionalities.
 */
contract EnhancedDynamicESIMNFT is ERC721, Ownable, ReentrancyGuard {
    /**
     * @dev Struct to hold ESIM details.
     */
    struct ESIM {
        uint256 id;
        address owner;
        string status;
        string metadata;
    }

    /**
     * @dev Mapping of ESIM ID to ESIM struct.
     */
    mapping(uint256 => ESIM) private esims;

    /**
     * @dev Constructor to initialize the contract with the name and symbol.
     */
    constructor() ERC721("DynamicESIMNFT", "DESIM") { }

    /**
     * @dev Function to mint a new ESIM NFT.
     * @param _id The ID of the ESIM.
     * @param _to The address to mint the ESIM to.
     * @param metadata The metadata of the ESIM.
     */
    function mintESIM(uint256 _id, address _to, string memory metadata) external onlyOwner nonReentrant {
        require(_id != 0, "ID must be non-zero");
        require(_to != address(0), "Invalid address");
        require(esims[_id].id == 0, "ESIM already exists");
        _safeMint(_to, _id);
        esims[_id] = ESIM(_id, _to, "Valid", metadata);
    }

    /**
     * @dev Function to update the status of an ESIM.
     * @param _id The ID of the ESIM.
     * @param _newStatus The new status of the ESIM.
     */
    function updateStatus(uint256 _id, string memory _newStatus) external nonReentrant {
        require(ownerOf(_id) == msg.sender, "Only the owner can update status");
        esims[_id].status = _newStatus;
    }

    /**
     * @dev Function to update the metadata of an ESIM.
     * @param _id The ID of the ESIM.
     * @param _newMetadata The new metadata of the ESIM.
     */
    function updateMetadata(uint256 _id, string memory _newMetadata) external nonReentrant {
        require(ownerOf(_id) == msg.sender, "Only the owner can update metadata");
        esims[_id].metadata = _newMetadata;
    }

    /**
     * @dev Function to get the details of an ESIM.
     * @param _id The ID of the ESIM.
     * @return The ESIM struct.
     */
    function getESIM(uint256 _id) external view returns (ESIM memory) {
        return esims[_id];
    }
}
