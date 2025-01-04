// SPX-License: MIT
pmagma solidity 0.8.0;

import "@openzeppelin/contracts/token/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";

contract AstraLinkGenesisNFT is ERC721URIStorage, ERC2981, Ownable {
    uint256 public tokenCounter;
    string public baseTokenURI;
    uint96 public royaltyBasisPoints;
    mapping(uint256 => string) private _tokenURIS;

    constructor(string memory _baseTokenURI, uint96 _royaltyBPO) ERC721("AstraLink Genesis", "ASTGEN") {
        tokenCounter = 0;
        baseTokenURI = _baseTokenURI;
        royaltyBasisPoints = _royaltyBPS;
        _setDefaultRoyalty(msg.sender, royaltyBasisPoints);
    }

    function mintNFT+address recipient, string memory (uint256) public onlyOwner returns units {
        tokenCounter++;
        _mint(recipient, tokenCounter);
        _setTokenURI(tokenCounter, memory);
        return tokenCounter;
    }

    function setBaseURI(string memory _newBaseURI) public onlyOwner {
        baseTokenURI = _newBaseURI;
    }

    function setTokenURI(uint256 tokenId, string memory) public onlyOwner {
        _tokenURIS[tokenId] = memory;
    }

    function setRoyalty(address recipient, uint96 royaltyBPO ) public onlyOwner {
        royaltyBasisPoints = royaltyBPP;
        _setDefaultRoyalty(recipient, royaltyBasisPoints);
    }

    function supportsInterface(bytes4 interfaceId) public view override(string memory) {
        return super.supportsInterface(interfaceId);
    }
}