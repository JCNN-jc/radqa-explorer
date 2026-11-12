// Optional end-to-end checks. Run from the project root with the app running.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function main() {
  const options = { headless: true, args: ['--no-sandbox'] };
  if (process.env.RADQA_BROWSER_EXECUTABLE) {
    options.executablePath = process.env.RADQA_BROWSER_EXECUTABLE;
  }
  const browser = await chromium.launch(options);
  const results = [];
  const output = path.resolve('verification/exports');
  fs.mkdirSync(output, { recursive: true });
  const fixture = name => path.resolve('data/fixtures', name);
  const url = process.env.RADQA_TEST_URL || 'http://localhost:8501';

  async function pageWithDefault() {
    const page = await browser.newPage({ acceptDownloads: true });
    await page.goto(url);
    await page.getByText('11 mm', { exact: true }).waitFor();
    return page;
  }
  async function source(page, value) {
    await page.getByRole('combobox').click();
    await page.getByRole('option', { name: value, exact: true }).click();
  }
  async function metric(page, label, expected) {
    await page.locator('[data-testid="stMetric"]').filter({ hasText: label })
      .getByText(expected, { exact: true }).waitFor();
  }
  const deltaLabel = 'ΔR80 (current − reference)';
  const comparisonButton = page => page.getByRole('button', {
    name: 'Download comparison results (CSV)', exact: true,
  });
  const cases = [
    { id: 'CMP01', name: 'positive', current: 'upload_shifted_curve.csv', reference: null,
      currentR80: '13 mm', referenceR80: '11 mm', delta: '+2 mm', expectedDelta: 2 },
    { id: 'CMP02', name: 'negative', current: null, reference: 'upload_shifted_curve.csv',
      currentR80: '11 mm', referenceR80: '13 mm', delta: '-2 mm', expectedDelta: -2 },
    { id: 'CMP03', name: 'zero', current: null, reference: null,
      currentR80: '11 mm', referenceR80: '11 mm', delta: '+0 mm', expectedDelta: 0 },
    { id: 'CMP04', name: 'current_missing', current: 'upload_no_crossing.csv', reference: null,
      currentR80: 'Not evaluable', referenceR80: '11 mm', delta: 'Not evaluable', expectedDelta: null },
    { id: 'CMP05', name: 'reference_missing', current: null, reference: 'upload_no_crossing.csv',
      currentR80: '11 mm', referenceR80: 'Not evaluable', delta: 'Not evaluable', expectedDelta: null },
  ];

  try {
    for (const test of cases) {
      const page = await pageWithDefault();
      try {
        if (test.current) {
          await page.locator('input[type=file]').first().setInputFiles(fixture(test.current));
          await page.getByText('Current file: ' + test.current, { exact: true }).waitFor();
        }
        await source(page, test.reference ? 'Upload reference CSV' : 'Bundled synthetic teaching data');
        if (test.reference) {
          await page.locator('input[type=file]').nth(1).setInputFiles(fixture(test.reference));
        }
        await metric(page, deltaLabel, test.delta);
        await metric(page, 'Reference distal R80', test.referenceR80);
        await page.locator('[data-testid="stMetric"]').filter({ hasText: /^Distal R80/ })
          .getByText(test.currentR80, { exact: true }).waitFor();
        await page.locator('img').first().waitFor();
        await page.waitForFunction(() => Array.from(document.images)
          .some(image => image.complete && image.naturalWidth > 0));
        const downloadEvent = page.waitForEvent('download');
        await comparisonButton(page).click();
        const filename = test.id + '_' + test.name + '.csv';
        await (await downloadEvent).saveAs(path.join(output, filename));
        results.push({ ...test, current: test.current || 'day3_handcheck_curve.csv',
          reference: test.reference || 'day3_handcheck_curve.csv',
          referenceSource: test.reference ? 'User-uploaded data' : 'Synthetic teaching data',
          observedCurrentR80: test.currentR80, observedReferenceR80: test.referenceR80,
          observedDelta: test.delta, chartLoaded: true, exportFile: filename, status: 'PASS' });
      } finally { await page.close(); }
    }

    const invalid = [
      ['missing_column', /Missing required column/],
      ['nonnumeric', /Row 3.*non-numeric/],
      ['duplicate_depth', /Row 4 repeats depth 10 mm/],
      ['unordered_depth', /not increasing at row 4/],
    ];
    for (const role of ['current', 'reference']) {
      for (const [name, message] of invalid) {
        const page = await pageWithDefault();
        try {
          // Begin with valid results so this also checks that old outputs disappear.
          if (role === 'current') {
            await source(page, 'Bundled synthetic teaching data');
          } else {
            await source(page, 'Upload reference CSV');
            await page.locator('input[type=file]').nth(1)
              .setInputFiles(fixture('day3_handcheck_curve.csv'));
          }
          await metric(page, deltaLabel, '+0 mm');
          const filename = 'upload_invalid_' + name + '.csv';
          await page.locator('input[type=file]').nth(role === 'current' ? 0 : 1)
            .setInputFiles(fixture(filename));
          const error = page.getByText('Cannot analyze ' + role + ' CSV:', { exact: false });
          await error.waitFor();
          const text = await error.innerText();
          if (!message.test(text)) throw Error('Unexpected error: ' + text);
          await comparisonButton(page).waitFor({ state: 'hidden' });
          await page.getByRole('button', { name: 'Download analysis results (CSV)', exact: true })
            .waitFor({ state: 'hidden' });
          await page.locator('[data-testid="stMetric"]').first().waitFor({ state: 'hidden' });
          await page.locator('img').first().waitFor({ state: 'hidden' });
          results.push({ id: 'INPUT_' + role.toUpperCase() + '_' + name.toUpperCase(),
            role, file: filename, expected: 'Specific error; no metrics, chart, or downloads',
            observed: text, staleOutputsCleared: true, status: 'PASS' });
        } finally { await page.close(); }
      }
    }
  } finally { await browser.close(); }
  return results;
}

main().then(results => {
  fs.writeFileSync('verification/browser_results.json', JSON.stringify(results, null, 2));
  console.log(JSON.stringify({ status: 'PASS', checks: results.length }));
}).catch(error => { console.error(error); process.exitCode = 1; });
