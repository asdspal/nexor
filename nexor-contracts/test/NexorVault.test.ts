import { expect } from "chai";
import { ethers } from "hardhat";
import { anyValue } from "@nomicfoundation/hardhat-chai-matchers/withArgs";

import type { Signer } from "ethers";

describe("NexorVault", () => {
  let owner: Signer;
  let operator: Signer;
  let user: Signer;

  beforeEach(async () => {
    [owner, operator, user] = await ethers.getSigners();
  });

  async function deployVault() {
    const Vault = await ethers.getContractFactory("NexorVault", owner);
    const vault = (await Vault.deploy(await operator.getAddress())) as any;
    return vault;
  }

  it("allows only operator/owner to execute strategies and bubbles reverts", async () => {
    const vault = await deployVault();

    const Target = await ethers.getContractFactory("StrategyTarget");
    const target = (await Target.deploy()) as any;

    const setValueCall = ethers.AbiCoder.defaultAbiCoder().encode(
      ["tuple(address to,uint256 value,bytes data)"],
      [
        {
          to: await target.getAddress(),
          value: 0,
          data: target.interface.encodeFunctionData("setValue", [42]),
        },
      ],
    );

    await expect(
      vault.connect(user).executeStrategy([setValueCall])
    ).to.be.revertedWithCustomError(vault, "OnlyVault");

    await expect(
      vault.connect(operator).executeStrategy([setValueCall])
    )
      .to.emit(vault, "StrategyCallExecuted")
      .withArgs(await target.getAddress(), 0, target.interface.encodeFunctionData("setValue", [42]), anyValue);

    expect(await target.value()).to.equal(42);

    const revertCall = ethers.AbiCoder.defaultAbiCoder().encode(
      ["tuple(address to,uint256 value,bytes data)"],
      [
        {
          to: await target.getAddress(),
          value: 0,
          data: target.interface.encodeFunctionData("revertAlways"),
        },
      ],
    );

    await expect(vault.connect(operator).executeStrategy([revertCall])).to.be.revertedWith(
      "StrategyTarget: revertAlways"
    );
  });

  it("accounts and withdraws yield", async () => {
    const vault = await deployVault();

    // Fund vault with native token to simulate yield
    await owner.sendTransaction({
      to: await vault.getAddress(),
      value: ethers.parseEther("1"),
    });

    await vault.connect(operator).accumulateYield();
    expect(await vault.accumulatedYield()).to.equal(ethers.parseEther("1"));

    const userAddress = await user.getAddress();
    const before = await ethers.provider.getBalance(userAddress);

    await expect(
      vault.withdrawYield(userAddress, ethers.parseEther("0.4"))
    )
      .to.emit(vault, "YieldWithdrawn")
      .withArgs(userAddress, ethers.parseEther("0.4"));

    expect(await vault.accumulatedYield()).to.equal(ethers.parseEther("0.6"));

    const after = await ethers.provider.getBalance(userAddress);
    expect(after - before).to.equal(ethers.parseEther("0.4"));
  });
});
