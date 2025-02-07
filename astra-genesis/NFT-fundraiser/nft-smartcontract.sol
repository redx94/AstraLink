// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";

contract AstraLinkGenesisNFT is ERC721URIStorage, ERC2981, Ownable {
    uint256 public tokenCounter;
    string public baseTokenURI;
    uint96 public royaltyBasisPoints;
    mapping(uint256 => string) private _tokenURIS;

    constructor(string memory _baseTokenURI, uint96 _royaltyBPS) ERC721("AstraLink Genesis", "ASTGEN") {
        tokenCounter = 0;
        baseTokenURI = _baseTokenURI;
        royaltyBasisPoints = _royaltyBPS;
        _setDefaultRoyalty(msg.sender, royaltyBasisPoints);
    }

    function mintNFT(address recipient, string memory tokenURI) public onlyOwner returns (uint256) {
        tokenCounter++;
        _mint(recipient, tokenCounter);
        _setTokenURI(tokenCounter, tokenURI);
        return tokenCounter;
    }

    function setBaseURI(string memory _newBaseURI) public onlyOwner {
        baseTokenURI = _newBaseURI;
    }

    function setTokenURI(uint256 tokenId, string memory tokenURI) public onlyOwner {
        _tokenURIS[tokenId] = tokenURI;
    }

    function setRoyalty(address recipient, uint96 royaltyBPS) public onlyOwner {
        royaltyBasisPoints = royaltyBPS;
        _setDefaultRoyalty(recipient, royaltyBasisPoints);
    }

    function supportsInterface(bytes4 interfaceId) public view override returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
