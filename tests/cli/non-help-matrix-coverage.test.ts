import { describe, expect, test } from "bun:test";

import {
  buildNonHelpCommandMatrix,
  listCommandNodes,
} from "../fixtures/golden-parity/non-help-matrix";

describe("cli non-help matrix coverage", () => {
  test("covers parser error branches for root and all command nodes", () => {
    const matrix = buildNonHelpCommandMatrix();
    const matrixById = new Set(matrix.map((item) => item.id));
    const nodes = listCommandNodes();

    expect(matrixById.has("root-invalid-option")).toBe(true);

    for (const node of nodes) {
      const nodeId = node.path.join("-");
      expect(matrixById.has(`${nodeId}-invalid-option`)).toBe(true);
      if (node.requiredArgCount > 0) {
        expect(matrixById.has(`${nodeId}-missing-required-args`)).toBe(true);
      }
    }
  });

  test("includes deterministic non-help functional baseline cases", () => {
    const matrixById = new Set(
      buildNonHelpCommandMatrix().map((item) => item.id),
    );

    expect(matrixById.has("version-long")).toBe(true);
    expect(matrixById.has("version-short")).toBe(true);
    expect(matrixById.has("derive-tests-single-file")).toBe(true);
    expect(matrixById.has("derive-tests-missing-path")).toBe(true);
  });
});
