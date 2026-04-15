import { expect } from "chai";
import { ethers } from "hardhat";

describe("NexorIntegration", function () {
  const dummyProof = {
    a: [1n, 2n],
    b: [
      [3n, 4n],
      [5n, 6n],
    ],
    c: [7n, 8n],
  } as const;

  async function deployStack() {
    const [owner, vault, borrower, liquidator] = await ethers.getSigners();

    const MockVerifier = await ethers.getContractFactory("MockGroth16Verifier");
    const verifier = await MockVerifier.deploy();

    const NexorCredit = await ethers.getContractFactory("NexorCredit");
    const credit = (await NexorCredit.deploy(await verifier.getAddress())) as any;

    const NexorLend = await ethers.getContractFactory("NexorLend");
    const lend = (await NexorLend.deploy(await credit.getAddress(), vault.address)) as any;

    return { owner, vault, borrower, liquidator, verifier, credit, lend };
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

  it("flows: proof-backed mint -> borrow -> repay", async function () {
    const { credit, lend, borrower } = await deployStack();
    const band = 3; // Band B => 130% ratio

    await mintBand(credit, borrower, band);
    expect(await credit.creditBandOf(borrower.address)).to.equal(band);

    const amount = 100;
    const collateral = 130; // exactly 130%

    await expect(lend.connect(borrower).borrow(amount, collateral))
      .to.emit(lend, "Borrowed")
      .withArgs(1, borrower.address, amount, collateral, band, 130);

    const loan = await lend.getLoan(1);
    expect(loan.borrower).to.equal(borrower.address);
    expect(loan.principal).to.equal(amount);
    expect(loan.collateral).to.equal(collateral);
    expect(loan.repaid).to.equal(false);
    expect(loan.liquidated).to.equal(false);

    await expect(lend.connect(borrower).repay(1, amount))
      .to.emit(lend, "Repaid")
      .withArgs(1, borrower.address, amount);

    const closed = await lend.getLoan(1);
    expect(closed.repaid).to.equal(true);
    expect(closed.liquidated).to.equal(false);
  });

  it("enforces band-based collateral ratio (Band B = 130%)", async function () {
    const { credit, lend, borrower } = await deployStack();
    const band = 3;
    await mintBand(credit, borrower, band);

    await expect(lend.connect(borrower).borrow(100, 129)).to.be.revertedWith(
      "NexorLend: insufficient collateral"
    );

    await lend.connect(borrower).borrow(100, 130);
    const loan = await lend.getLoan(1);
    expect(loan.collateral).to.equal(130);
  });

  it("blocks liquidation when health factor >= 1", async function () {
    const { credit, lend, borrower, liquidator } = await deployStack();
    const band = 4; // Band A => 120%
    await mintBand(credit, borrower, band);

    await lend.connect(borrower).borrow(100, 120);

    // currentCollateralValue equal to required keeps health factor at 1
    await expect(
      lend.connect(liquidator).liquidate(1, 120)
    ).to.be.revertedWith("NexorLend: healthy");
  });

  it("allows liquidation when health factor falls below 1", async function () {
    const { credit, lend, borrower, liquidator } = await deployStack();
    const band = 4; // Band A => 120%
    await mintBand(credit, borrower, band);

    await lend.connect(borrower).borrow(100, 120);

    await expect(lend.connect(liquidator).liquidate(1, 119)).to.emit(
      lend,
      "Liquidated"
    );

    const loan = await lend.getLoan(1);
    expect(loan.liquidated).to.equal(true);
    expect(loan.repaid).to.equal(false);
  });
});
