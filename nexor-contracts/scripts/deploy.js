const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deployer:", deployer.address);

  // 1) Deploy Groth16Verifier (no constructor args)
  const Verifier = await hre.ethers.getContractFactory("Groth16Verifier");
  const verifier = await Verifier.deploy();
  await verifier.waitForDeployment();
  const verifierAddress = await verifier.getAddress();
  console.log("Groth16Verifier deployed at:", verifierAddress);

  // 2) Deploy NexorCredit with verifier address
  const Credit = await hre.ethers.getContractFactory("NexorCredit");
  const credit = await Credit.deploy(verifierAddress);
  await credit.waitForDeployment();
  const creditAddress = await credit.getAddress();
  console.log("NexorCredit deployed at:", creditAddress);

  // 3) Deploy NexorLend with credit address and vault (use deployer as placeholder vault)
  const vault = process.env.NEXOR_VAULT_ADDRESS || deployer.address;
  const Lend = await hre.ethers.getContractFactory("NexorLend");
  const lend = await Lend.deploy(creditAddress, vault);
  await lend.waitForDeployment();
  const lendAddress = await lend.getAddress();
  console.log("NexorLend deployed at:", lendAddress);

  // Emit JSON for scripting
  console.log(JSON.stringify({
    network: hre.network.name,
    verifier: verifierAddress,
    credit: creditAddress,
    lend: lendAddress,
    vault,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
