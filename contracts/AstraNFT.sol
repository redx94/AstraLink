// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IAstraNFT {
    function createNFT(address to, string memory metadata) external returns (uint256);
    function transferNFT(address from, address to, uint256 tokenId) external;
    function getOwner(uint256 tokenId) external view returns (address);
}
