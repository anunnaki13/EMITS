const { test, expect } = require("@playwright/test");

const pages = [
  {
    name: "dashboard",
    path: "/dashboard",
    anchors: [
      { testId: "dashboard-page" },
      { text: /Dashboard Operasional Bahan Bakar/i },
      { text: /Monitoring Stock|Stok/i },
      { text: /Jadwal|Realisasi/i },
      { text: /Dispute|Umpire/i }
    ]
  },
  {
    name: "management-report",
    path: "/laporan?tab=management",
    anchors: [
      { testId: "laporan-page" },
      { text: /Laporan Data/i },
      { testId: "export-btn" },
      { text: /Manajemen/i },
      { text: /Stock Saat Ini|Monitoring Stock/i }
    ]
  },
  {
    name: "data-quality",
    path: "/data-quality",
    anchors: [
      { testId: "data-quality-page" },
      { text: /Data Quality Monitor/i },
      { text: /Export|Perbarui|Refresh|Rule|Kualitas/i }
    ]
  },
  {
    name: "dispute-monitor",
    path: "/dispute-monitor",
    anchors: [
      { text: /Dispute Monitor/i },
      { text: /Total Dispute|Umpire|Critical|Warning/i },
      { text: /Tutup Dispute|Tambah Catatan|Tidak ada data dispute|Supplier/i }
    ]
  },
  {
    name: "settings-runtime-status",
    path: "/settings",
    anchors: [
      { testId: "settings-page" },
      { text: /Pengaturan/i },
      { text: /Status Operasional/i },
      { text: /Refresh|Runtime status|Backend|Frontend/i }
    ]
  }
];

async function authenticate(page) {
  const token = process.env.VISUAL_SMOKE_TOKEN;
  const email = process.env.VISUAL_SMOKE_EMAIL;
  const password = process.env.VISUAL_SMOKE_PASSWORD;

  if (token) {
    await page.addInitScript((rawToken) => {
      localStorage.setItem("token", rawToken.replace(/^Bearer\s+/i, ""));
    }, token);
    return;
  }

  if (!email || !password) {
    test.skip(true, "Set VISUAL_SMOKE_TOKEN or VISUAL_SMOKE_EMAIL/VISUAL_SMOKE_PASSWORD to run authenticated visual smoke tests.");
  }

  await page.goto("/login");
  await page.getByTestId("login-email-input").fill(email);
  await page.getByTestId("login-password-input").fill(password);
  await page.getByTestId("login-submit-btn").click();
  await expect(page).toHaveURL(/\/dashboard/);
}

function locatorFor(page, anchor) {
  if (anchor.testId) return page.getByTestId(anchor.testId);
  return page.getByText(anchor.text).first();
}

async function assertNoHorizontalOverflow(page) {
  const overflow = await page.evaluate(() => {
    return document.documentElement.scrollWidth - window.innerWidth;
  });
  expect(overflow, "page should not render horizontal overflow").toBeLessThanOrEqual(8);
}

async function assertNoObviousTextCollision(page) {
  const collisions = await page.evaluate(() => {
    const isVisible = (element) => {
      const style = window.getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      const text = (element.innerText || element.textContent || "").trim();
      const centerX = Math.min(Math.max(rect.left + rect.width / 2, 0), window.innerWidth - 1);
      const centerY = Math.min(Math.max(rect.top + rect.height / 2, 0), window.innerHeight - 1);
      const topElement = document.elementFromPoint(centerX, centerY);
      return (
        text.length > 0 &&
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        Number(style.opacity) !== 0 &&
        rect.width > 0 &&
        rect.height > 0 &&
        rect.bottom >= 0 &&
        rect.top <= window.innerHeight &&
        topElement &&
        (element === topElement || element.contains(topElement) || topElement.contains(element))
      );
    };

    const elements = Array.from(document.querySelectorAll("h1,h2,h3,p,span,label,button,a,th,td"))
      .filter(isVisible)
      .slice(0, 350);

    const failures = [];

    for (let i = 0; i < elements.length; i += 1) {
      for (let j = i + 1; j < elements.length; j += 1) {
        const first = elements[i];
        const second = elements[j];
        if (first.contains(second) || second.contains(first)) continue;

        const a = first.getBoundingClientRect();
        const b = second.getBoundingClientRect();
        const overlapX = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left));
        const overlapY = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
        const minWidth = Math.min(a.width, b.width);
        const minHeight = Math.min(a.height, b.height);

        if (overlapX > minWidth * 0.7 && overlapY > minHeight * 0.7) {
          failures.push({
            first: (first.innerText || first.textContent || "").trim().slice(0, 60),
            second: (second.innerText || second.textContent || "").trim().slice(0, 60)
          });
        }

        if (failures.length >= 5) return failures;
      }
    }

    return failures;
  });

  expect(collisions, "visible text should not obviously collide").toEqual([]);
}

test.beforeEach(async ({ page }) => {
  await authenticate(page);
});

for (const item of pages) {
  test(`${item.name} visual smoke`, async ({ page }, testInfo) => {
    await page.goto(item.path);
    await page.waitForLoadState("domcontentloaded");

    await expect(page, "authenticated smoke should not land on login").not.toHaveURL(/\/login/);

    for (const anchor of item.anchors) {
      await expect(locatorFor(page, anchor)).toBeVisible();
    }

    const bodyTextLength = await page.locator("body").innerText().then((text) => text.trim().length);
    expect(bodyTextLength, "page body should not be blank").toBeGreaterThan(120);

    await assertNoHorizontalOverflow(page);
    await assertNoObviousTextCollision(page);

    await page.screenshot({
      path: testInfo.outputPath(`${item.name}.png`),
      fullPage: true,
      animations: "disabled"
    });
  });
}
