import { expect } from "chai";
import { ethers } from "hardhat";

describe("NexorCredit", function () {
  async function deployFixture() {
    const [owner, user, other] = await ethers.getSigners();

    const MockVerifier = await ethers.getContractFactory("MockGroth16Verifier");
    const verifier = await MockVerifier.deploy();

    const NexorCredit = await ethers.getContractFactory("NexorCredit");
    const credit = await NexorCredit.deploy(await verifier.getAddress());

    return { owner, user, other, verifier, credit };
  }

  const dummyProof = {
    a: [1n, 2n],
    b: [
      [3n, 4n],
      [5n, 6n],
    ],
    c: [7n, 8n],
  } as const;

  it("mints a locked SBT when proof valid and band matches", async function () {
    const { credit, user } = await deployFixture();

    const band = 3;
    const pubSignals: [bigint, bigint] = [BigInt(band), 0n];

    const tx = await credit.mintCreditBand(
      user.address,
      band,
      dummyProof.a,
      dummyProof.b,
      dummyProof.c,
      pubSignals
    );

    const receipt = await tx.wait();
    const tokenId = BigInt(user.address);

    await expect(tx)
      .to.emit(credit, "CreditBandMinted")
      .withArgs(user.address, band, tokenId);

    expect(await credit.ownerOf(tokenId)).to.equal(user.address);
    expect(await credit.creditBandOf(user.address)).to.equal(band);
    expect(await credit.locked(tokenId)).to.equal(true);
  });

  it("reverts on band mismatch", async function () {
    const { credit, user } = await deployFixture();
    const band = 2;
    const pubSignals: [bigint, bigint] = [5n, 0n];

    await expect(
      credit.mintCreditBand(
        user.address,
        band,
        dummyProof.a,
        dummyProof.b,
        dummyProof.c,
        pubSignals
      )
    ).to.be.revertedWith("NexorCredit: band mismatch");
  });

  it("reverts when already minted", async function () {
    const { credit, user } = await deployFixture();
    const band = 4;
    const pubSignals: [bigint, bigint] = [BigInt(band), 0n];

    await credit.mintCreditBand(
      user.address,
      band,
      dummyProof.a,
      dummyProof.b,
      dummyProof.c,
      pubSignals
    );

    await expect(
      credit.mintCreditBand(
        user.address,
        band,
        dummyProof.a,
        dummyProof.b,
        dummyProof.c,
        pubSignals
      )
    ).to.be.revertedWith("NexorCredit: already minted");
  });

  it("reverts when verifier fails", async function () {
    const { credit, user, verifier } = await deployFixture();
    const band = 1;
    const pubSignals: [bigint, bigint] = [BigInt(band), 0n];

    await verifier.setShouldVerify(false);

    await expect(
      credit.mintCreditBand(
        user.address,
        band,
        dummyProof.a,
        dummyProof.b,
        dummyProof.c,
        pubSignals
      )
    ).to.be.revertedWith("Invalid proof");
  });

  it("blocks transfers and approvals (ERC-5192 behavior)", async function () {
    const { credit, user, other } = await deployFixture();
    const band = 2;
    const pubSignals: [bigint, bigint] = [BigInt(band), 0n];

    await credit.mintCreditBand(
      user.address,
      band,
      dummyProof.a,
      dummyProof.b,
      dummyProof.c,
      pubSignals
    );

    const tokenId = BigInt(user.address);

    await expect(
      (credit as any)
        .connect(user)
        ["transferFrom(address,address,uint256)"](user.address, other.address, tokenId)
    ).to.be.revertedWith("ERC5192: transfers are locked");

    await expect(
      (credit as any).connect(user)["approve(address,uint256)"](other.address, tokenId)
    ).to.be.revertedWith("ERC5192: approvals disabled");

    await expect(
      (credit as any).connect(user)["setApprovalForAll(address,bool)"](other.address, true)
    ).to.be.revertedWith("ERC5192: approvals disabled");
  });
});
