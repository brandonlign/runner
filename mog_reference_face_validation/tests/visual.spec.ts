import { expect, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";

const output = "artifacts";

test.beforeAll(async () => {
  await mkdir(output, { recursive: true });
});

test("front and side structure and clay views render naturally", async ({ page }) => {
  await page.goto("/");
  const section = page.locator("#ideal-reference");
  await expect(section).toBeVisible();
  await expect(page.getByText("+5° canthal tilt", { exact: true })).toBeVisible();
  await expect(section.locator("svg")).toHaveAttribute("aria-label", "Front target face in structure mode");
  await section.screenshot({ path: `${output}/front-structure.png` });

  await page.getByRole("button", { name: "Clay" }).click();
  await expect(section.locator("svg")).toHaveAttribute("aria-label", "Front target face in rendered mode");
  await section.screenshot({ path: `${output}/front-realistic.png` });

  await page.getByRole("button", { name: "Side" }).click();
  await expect(section.locator("svg")).toHaveAttribute("aria-label", "Profile target face in rendered mode");
  await section.screenshot({ path: `${output}/side-realistic.png` });

  await page.getByRole("button", { name: "Structure" }).click();
  await expect(section.locator("svg")).toHaveAttribute("aria-label", "Profile target face in structure mode");
  await section.screenshot({ path: `${output}/side-structure.png` });
});
