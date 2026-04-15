import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import * as dotenv from "dotenv";

dotenv.config();

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.25",
    settings: {
      evmVersion: "cancun",
    },
  },
  networks: {
    hashkey_testnet: {
      url: process.env.HASHKEY_RPC_URL || "",
      chainId: 133,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
    },
  },
  etherscan: {
    // Blockscout-compatible; adjust URLs if explorer endpoints differ
    apiKey: {
      hashkey_testnet: process.env.HASHKEY_EXPLORER_API_KEY || "",
    },
    customChains: [
      {
        network: "hashkey_testnet",
        chainId: 133,
        urls: {
          apiURL:
            process.env.HASHKEY_EXPLORER_API_URL ||
            "https://explorer-api-testnet.hashkeychain.com/api",
          browserURL:
            process.env.HASHKEY_EXPLORER_BROWSER_URL ||
            "https://explorer-testnet.hashkeychain.com",
        },
      },
    ],
  },
};

export default config;
