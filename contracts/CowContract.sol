// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

interface IGnosisSettlement{
    function setPreSignature(
        bytes calldata orderUid, 
        bool signed) external;
}


contract CowContract {

    address owner;
    address gnosisSettlement = 0x9008D19f58AAbD9eD0D60971565AA8510560ab41;

    constructor(){
        owner = msg.sender;
    }

    function sendSetSignatureTx(
        bytes calldata orderUid, 
        bool signed) 
        external
    {
        require(msg.sender == owner, "NotOwner");
        IGnosisSettlement(gnosisSettlement).setPreSignature(orderUid,signed);
    }   

}