
// AstraLink NFT Contract
// Author: Reece Dixon

// Copyright (C) 2025 Reece Dixon
// License: Refer to the License file.

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Burnable.sol";

/* Simple ERC-721 contract with create methods */
contract AstraNFT is ERC721, ERC721Burnable {
    string public secretURI;

    // Events
    event NewOwner(string secretURI, address indexed owner, string metadata);

    /* Permits a user to be the owner of a given original mint id. */
    function createNFT(address to, string metadata) external returns (uint256);

    /* Gets the owner of an NFT.
     * The returned address is and sees.
     */
    function getObjectId() external view returns (uint256);
}
