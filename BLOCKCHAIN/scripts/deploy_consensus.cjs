const hre = require("hardhat");

async function main() {
    const Consensus = await hre.ethers.getContractFactory("NIDSGlobalConsensus");
    const consensus = await Consensus.deploy();

    await consensus.waitForDeployment();

    const address = await consensus.getAddress();
    console.log("NIDSGlobalConsensus deployed to:", address);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
