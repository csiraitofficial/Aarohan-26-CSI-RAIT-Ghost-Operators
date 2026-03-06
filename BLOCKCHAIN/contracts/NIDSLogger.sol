// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract NIDSLogger {

    struct Alert {
        string ip;
        string attack;
        uint256 timestamp;
    }

    Alert[] public alerts;

    event AlertStored(
        string ip,
        string attack,
        uint256 timestamp
    );

    function storeAlert(
        string memory ip,
        string memory attack
    ) public {

        alerts.push(
            Alert({
                ip: ip,
                attack: attack,
                timestamp: block.timestamp
            })
        );

        emit AlertStored(
            ip,
            attack,
            block.timestamp
        );
    }

    function getAlert(uint256 index)
        public
        view
        returns (
            string memory,
            string memory,
            uint256
        )
    {
        Alert memory a = alerts[index];
        return (
            a.ip,
            a.attack,
            a.timestamp
        );
    }

    function totalAlerts() public view returns(uint256) {
        return alerts.length;
    }
}