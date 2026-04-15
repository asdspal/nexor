// CreditScore.circom
// Blueprint Section 6.1: Credit score band logic
// Band A (3): tx_count >= 100, repayment_ratio >= 95, liquidation_count == 0
// Band B (2): tx_count >= 50,  repayment_ratio >= 80, liquidation_count <= 1
// Band C (1): tx_count >= 20,  repayment_ratio >= 60
// Band D (0): otherwise

pragma circom 2.1.0;

include "comparators.circom";
include "mux1.circom";

template CreditScore() {
    // Private inputs
    signal input tx_count;           // total transactions
    signal input avg_balance_tier;   // kept for compatibility with blueprint input schema (unused in band logic)
    signal input repayment_ratio;    // percentage 0-100
    signal input liquidation_count;  // total liquidations
    signal input nonce;              // proof nonce

    // Public outputs
    signal output credit_band;       // 0..3
    signal output proof_nonce;       // mirrors nonce

    // Comparators (32-bit wide for safety on all integer inputs)
    component lt_tx_100 = LessThan(32);
    lt_tx_100.in[0] <== tx_count;
    lt_tx_100.in[1] <== 100;
    signal ge_tx_100;
    ge_tx_100 <== 1 - lt_tx_100.out;

    component lt_tx_50 = LessThan(32);
    lt_tx_50.in[0] <== tx_count;
    lt_tx_50.in[1] <== 50;
    signal ge_tx_50;
    ge_tx_50 <== 1 - lt_tx_50.out;

    component lt_tx_20 = LessThan(32);
    lt_tx_20.in[0] <== tx_count;
    lt_tx_20.in[1] <== 20;
    signal ge_tx_20;
    ge_tx_20 <== 1 - lt_tx_20.out;

    component lt_repay_95 = LessThan(32);
    lt_repay_95.in[0] <== repayment_ratio;
    lt_repay_95.in[1] <== 95;
    signal ge_repay_95;
    ge_repay_95 <== 1 - lt_repay_95.out;

    component lt_repay_80 = LessThan(32);
    lt_repay_80.in[0] <== repayment_ratio;
    lt_repay_80.in[1] <== 80;
    signal ge_repay_80;
    ge_repay_80 <== 1 - lt_repay_80.out;

    component lt_repay_60 = LessThan(32);
    lt_repay_60.in[0] <== repayment_ratio;
    lt_repay_60.in[1] <== 60;
    signal ge_repay_60;
    ge_repay_60 <== 1 - lt_repay_60.out;

    component lt_liq_2 = LessThan(32);
    lt_liq_2.in[0] <== liquidation_count;
    lt_liq_2.in[1] <== 2; // liquidation_count <= 1  <=> liquidation_count < 2
    signal le_liq_1;
    le_liq_1 <== lt_liq_2.out;

    component is_liq_zero = IsZero();
    is_liq_zero.in <== liquidation_count;
    signal eq_liq_zero;
    eq_liq_zero <== is_liq_zero.out;

    // Condition flags
    // Enforce AND via multiplicative chaining with intermediate signals to keep constraints quadratic
    signal cond_band_a_step1;
    signal cond_band_a;
    cond_band_a_step1 <== ge_tx_100 * ge_repay_95;
    cond_band_a <== cond_band_a_step1 * eq_liq_zero;

    signal cond_band_b_step1;
    signal cond_band_b;
    cond_band_b_step1 <== ge_tx_50 * ge_repay_80;
    cond_band_b <== cond_band_b_step1 * le_liq_1;

    signal cond_band_c;
    cond_band_c <== ge_tx_20 * ge_repay_60;

    // Priority selection: A > B > C > D
    component mux_c = Mux1();
    mux_c.c[0] <== 0; // Band D default
    mux_c.c[1] <== 1; // Band C
    mux_c.s <== cond_band_c;

    component mux_b = Mux1();
    mux_b.c[0] <== mux_c.out; // either 0 or 1
    mux_b.c[1] <== 2;         // Band B
    mux_b.s <== cond_band_b;

    component mux_a = Mux1();
    mux_a.c[0] <== mux_b.out; // 0,1,2
    mux_a.c[1] <== 3;         // Band A
    mux_a.s <== cond_band_a;

    credit_band <== mux_a.out;

    // Expose nonce as public proof binding
    proof_nonce <== nonce;
}

component main = CreditScore();
