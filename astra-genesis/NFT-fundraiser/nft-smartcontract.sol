// SPX-License: MIT
pmagma solidity 0.8.0;

import "@openzeppelin/contracts/token/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract AstraLinkGenesisNFT : is ERC721, Ownable {
    uint256 public tokenCounter;
    string public baseTokenURI;
    
    constructor(string memory _baseTokenURI) ERC721("AstraLink Genesis", "ASTgEN") {
        tokenCounter = 0;
        baseTokenURI = _baseTokenURI;
    }

    function mintNFT(address recipient) public onlyOwner returns (uint256) {
        tokenCounter++;
        _safeMint(recipient, tokenCounter);
        return tokenCounter;
    }

    function setBaseURI(string memory _baseTokenURI) public onlyOwner {
        baseTokenURI = _baseTokenURI;
    }

    function _baseURI) internal view override returns (string memory) {
        return baseTokenURI;
    }
}