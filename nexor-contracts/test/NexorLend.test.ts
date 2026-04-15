import { expect } from "chai";
import { ethers } from "hardhat";

describe("NexorLend", function () {
  const dummyProof = {
    a: [1n, 2n],
    b: [
      [3n, 4n],
      [5n, 6n],
    ],
    c: [7n, 8n],
  } as const;

  async function deployFixture() {
    const [owner, vault, userA, userD, stranger] = await ethers.getSigners();

    const MockVerifier = await ethers.getContractFactory("MockGroth16Verifier");
    const verifier = await MockVerifier.deploy();

    const NexorCredit = await ethers.getContractFactory("NexorCredit");
    const credit = await NexorCredit.deploy(await verifier.getAddress());

    const NexorLend = await ethers.getContractFactory("NexorLend");
    const lend = await NexorLend.deploy(await credit.getAddress(), vault.address);

    return { owner, vault, userA, userD, stranger, verifier, credit, lend };
  }

  async function mintBand(credit: any, account: any, band: number) {
    const pubSignals: [bigint, bigint] = [BigInt(band), 0n];
    await credit.mintCreditBand(
      account.address,
      band,
      dummyProof.a,
      dummyProof.b,
      dummyProof.c,
      pubSignals
    );
  }

  it("allows Band A to borrow with 120% collateral", async function () {
    const { credit, lend, userA } = await deployFixture();
    await mintBand(credit, userA, 4); // Band A

    const tx = await lend.connect(userA).borrow(100, 120);
    const receipt = await tx.wait();

    const event = receipt!.logs
      .map((l: any) => lend.interface.parseLog(l).name)
      .includes("Borrowed");
    expect(event).to.equal(true);

    const loan = await lend.getLoan(1);
    expect(loan.principal).to.equal(100);
    expect(loan.collateral).to.equal(120);
  });

  it("requires Band D to post 150% collateral", async function () {
    const { credit, lend, userD } = await deployFixture();
    await mintBand(credit, userD, 1); // Band D

    await expect(lend.connect(userD).borrow(100, 149)).to.be.revertedWith(
      "NexorLend: insufficient collateral"
    );

    await lend.connect(userD).borrow(100, 150);
    const loan = await lend.getLoan(1);
    expect(loan.collateral).to.equal(150);
  });

  it("marks loans repaid by borrower", async function () {
    const { credit, lend, userA } = await deployFixture();
    await mintBand(credit, userA, 4);

    await lend.connect(userA).borrow(200, 240);
    await lend.connect(userA).repay(1, 200);

    const loan = await lend.getLoan(1);
    expect(loan.repaid).to.equal(true);
  });

  it("restricts autoRepay to vault or owner", async function () {
    const { credit, lend, userA, vault, stranger } = await deployFixture();
    await mintBand(credit, userA, 4);

    await lend.connect(userA).borrow(50, 60);

    await expect(lend.connect(stranger).autoRepay(1, 50)).to.be.revertedWith(
      "NexorLend: only vault or owner"
    );

    await lend.connect(vault).autoRepay(1, 50);
    const loan = await lend.getLoan(1);
    expect(loan.repaid).to.equal(true);
  });

  it("liquidates when health factor falls below 1", async function () {
    const { credit, lend, userA } = await deployFixture();
    await mintBand(credit, userA, 4); // 120% required

    await lend.connect(userA).borrow(100, 120);

    await expect(lend.liquidate(1, 120)).to.be.revertedWith("NexorLend: healthy");

    await lend.liquidate(1, 119);
    const loan = await lend.getLoan(1);
    expect(loan.liquidated).to.equal(true);
  });
});

