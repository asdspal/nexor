const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deployer:", deployer.address);

  // Resolve operator (ERC-4337 smart account / backend executor)
  const operator = process.env.NEXOR_VAULT_OPERATOR || deployer.address;
  if (!operator) throw new Error("NEXOR_VAULT_OPERATOR not set and deployer missing");

  const Vault = await hre.ethers.getContractFactory("NexorVault");
  const vault = await Vault.deploy(operator);
  await vault.waitForDeployment();
  const vaultAddress = await vault.getAddress();

  console.log("NexorVault deployed at:", vaultAddress);
  console.log(JSON.stringify({
    network: hre.network.name,
    vault: vaultAddress,
    operator,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

