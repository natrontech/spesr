import { expect, test } from "@playwright/test";
import { readFile } from "node:fs/promises";
import JSZip from "jszip";

test("expense controls remain usable", async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));

  // Keep the UI check independent of production data and authentication
  await page.addInitScript(() => {
    const payload = btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }));
    localStorage.setItem(
      "pocketbase_auth",
      JSON.stringify({
        token: `test.${payload}.test`,
        record: {
          id: "testuser0000001",
          collectionId: "users",
          collectionName: "users",
          name: "Test user",
          email: "test@example.test",
          avatar: "",
          admin: true
        }
      })
    );
  });
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const items = path.includes("/customers/")
      ? [{ id: "customer0000001", name: "Test customer" }]
      : path.includes("/expense_types/")
        ? [{ id: "expensetype0001", name: "Food" }]
        : [
            {
              id: "expense00000001",
              collectionId: "expenses",
              customer: "customer0000001",
              expense_type: "expensetype0001",
              user: "testuser0000001",
              datetime: new Date().toISOString(),
              created: new Date().toISOString(),
              amount: 25,
              description: "Test receipt",
              picture: "",
              company_credit_card: false,
              expand: {
                customer: { name: "Test customer" },
                expense_type: { name: "Food" },
                user: { name: "Test user" }
              }
            }
          ];
    await route.fulfill({ json: { page: 1, totalPages: 1, totalItems: items.length, items } });
  });

  // Exercise the migrated trigger, popover, calendar and command APIs together
  await page.goto("/app/");
  await page.getByRole("button", { name: "Add Expense", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Add Expense" });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Pick a date" }).click();
  await expect(page.getByRole("grid")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("expense-calendar.png") });
  await page.keyboard.press("Escape");
  await dialog.getByRole("combobox", { name: "Customer" }).click();
  await page.getByPlaceholder("Search customers...").fill("Test");
  await page.getByRole("option", { name: /Test customer/ }).click();
  await expect(dialog.getByRole("combobox", { name: "Customer" })).toBeVisible();
  await dialog.getByRole("checkbox").check();
  await expect(dialog.getByRole("checkbox")).toBeChecked();
  await dialog.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(dialog).toBeHidden();

  // Verify dismissal updates the drawer state so it can be opened again
  for (let attempt = 0; attempt < 2; attempt++) {
    await page.getByRole("button", { name: "Download CSV" }).click();
    const drawer = page.getByRole("dialog", { name: "Select Month and Year" });
    await expect(drawer).toBeVisible();
    await drawer.getByRole("button", { name: "Cancel", exact: true }).click();
    await expect(drawer).toBeHidden();
  }

  // Verify the export still creates a workbook containing the selected expenses
  await page.getByRole("button", { name: "Generate PDF Summary" }).click();
  const summary = page.getByRole("dialog", { name: "Generate Expense Summary" });
  for (let date = 0; date < 2; date++) {
    await summary.getByRole("button", { name: "Pick a date", exact: true }).first().click();
    await page.locator("[data-calendar-day][data-today]").click();
    await page.keyboard.press("Escape");
  }
  const downloadReady = page.waitForEvent("download");
  await summary.getByRole("button", { name: "Generate ZIP Package" }).click();
  const download = await downloadReady;
  const archive = await JSZip.loadAsync(await readFile((await download.path())!));
  const workbookFile = archive.file(/\.xlsx$/)[0];
  const workbook = await JSZip.loadAsync(await workbookFile.async("nodebuffer"));
  expect(await workbook.file("xl/sharedStrings.xml")!.async("string")).toContain("Test receipt");
  await expect(summary).toBeHidden();

  await page.getByRole("button", { name: "Toggle theme" }).click();
  await page.getByRole("menuitem", { name: "Dark", exact: true }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await page.screenshot({ path: testInfo.outputPath("expenses-dark.png") });
  expect(errors).toEqual([]);
});

test("login loads available authentication methods", async ({ page }) => {
  const authMethods = page.waitForRequest("**/api/collections/users/auth-methods*");
  await page.route("**/api/collections/users/auth-methods*", (route) =>
    route.fulfill({
      json: {
        password: { enabled: true, identityFields: ["email"] },
        oauth2: { enabled: false, providers: [] },
        mfa: { enabled: false },
        otp: { enabled: false }
      }
    })
  );
  await page.goto("/login/");
  await authMethods;
  await expect(page.getByRole("button", { name: "Log in", exact: true })).toBeVisible();
});
