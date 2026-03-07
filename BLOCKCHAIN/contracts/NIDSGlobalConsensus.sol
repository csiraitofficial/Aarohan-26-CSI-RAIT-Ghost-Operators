// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title NIDSGlobalConsensus
 * @dev Implements a decentralized voting mechanism for blocking malicious IPs based on anonymized hashes.
 */
contract NIDSGlobalConsensus {
    
    struct ThreatProposal {
        bytes32 ipHash;         // Hashed IP for privacy
        string category;        // Attack category (e.g., "SYN Flood")
        uint256 approveVotes;
        uint256 rejectVotes;
        uint256 timestamp;
        bool finalized;
        bool blocked;           // Final decision
    }

    mapping(uint256 => ThreatProposal) public proposals;
    mapping(bytes32 => bool) public globalBlockList;
    mapping(address => bool) public authorizedVoters;
    mapping(uint256 => mapping(address => bool)) public hasVoted;
    
    uint256 public proposalCount;
    address public admin;
    uint256 public constant VOTE_THRESHOLD = 3; // Example threshold

    event ThreatProposed(uint256 indexed id, bytes32 indexed ipHash, string category);
    event Voted(uint256 indexed id, address voter, bool approve);
    event ThreatFinalized(uint256 indexed id, bytes32 indexed ipHash, bool blocked);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }

    modifier onlyVoter() {
        require(authorizedVoters[msg.sender], "Not authorized voter");
        _;
    }

    constructor() {
        admin = msg.sender;
        authorizedVoters[msg.sender] = true;
    }

    function addVoter(address voter) external onlyAdmin {
        authorizedVoters[voter] = true;
    }

    /**
     * @dev Propose a new IP hash to be blocked.
     */
    function proposeThreat(bytes32 _ipHash, string memory _category) external onlyVoter {
        proposalCount++;
        proposals[proposalCount] = ThreatProposal({
            ipHash: _ipHash,
            category: _category,
            approveVotes: 0,
            rejectVotes: 0,
            timestamp: block.timestamp,
            finalized: false,
            blocked: false
        });

        emit ThreatProposed(proposalCount, _ipHash, _category);
    }

    /**
     * @dev Vote on a proposal. 
     */
    function vote(uint256 _id, bool _approve) external onlyVoter {
        ThreatProposal storage p = proposals[_id];
        require(!p.finalized, "Already finalized");
        require(!hasVoted[_id][msg.sender], "Already voted");

        if (_approve) {
            p.approveVotes++;
        } else {
            p.rejectVotes++;
        }

        hasVoted[_id][msg.sender] = true;
        emit Voted(_id, msg.sender, _approve);

        // Auto-finalize if threshold met
        if (p.approveVotes >= VOTE_THRESHOLD) {
            _finalize(_id, true);
        } else if (p.rejectVotes >= VOTE_THRESHOLD) {
            _finalize(_id, false);
        }
    }

    function _finalize(uint256 _id, bool _blocked) internal {
        ThreatProposal storage p = proposals[_id];
        p.finalized = true;
        p.blocked = _blocked;
        
        if (_blocked) {
            globalBlockList[p.ipHash] = true;
        }

        emit ThreatFinalized(_id, p.ipHash, _blocked);
    }

    /**
     * @dev Check if an IP hash is globally blocked.
     * NIDS nodes call this locally comparing keccak256(incomingIP)
     */
    function isGloballyBlocked(bytes32 _ipHash) external view returns (bool) {
        return globalBlockList[_ipHash];
    }
}
