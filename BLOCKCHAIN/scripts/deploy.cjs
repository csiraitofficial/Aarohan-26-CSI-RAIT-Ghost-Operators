const hre = require("hardhat");

async function main() {

    const Logger = await hre.ethers.getContractFactory("NIDSLogger");

    const logger = await Logger.deploy();

    await logger.waitForDeployment();

    const address = await logger.getAddress();

    console.log("NIDSLogger deployed to:", address);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});