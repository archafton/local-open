const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  try {
    const browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox'
      ]
    });

    const page = await browser.newPage();

    // Set User-Agent to mimic a real browser
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)');

    // Set extra headers if necessary
    await page.setExtraHTTPHeaders({
      'accept': 'application/json'
    });

    // Replace [YOUR_API_KEY] with your actual API key
    const apiKey = 'wY0po1XWU2fmT4TZ3er5ttthOAzjZPThy36mjMOS';
    const url = `https://api.congress.gov/v3/bill?api_key=${apiKey}&format=json&limit=20&sort=updateDate+desc`;
// https://api.congress.gov/v3/bill?api_key=wY0po1XWU2fmT4TZ3er5ttthOAzjZPThy36mjMOS&format=json&limit=20&sort=updateDate+desc
// https://api.congress.gov/v3/bill?api_key=${apiKey}&format=json&limit=20&sort=updateDate+desc
    // Navigate to the URL and wait until the network is idle
    await page.goto(url, { waitUntil: 'networkidle2' });

    // Extract the page content
    const content = await page.evaluate(() => document.body.innerText);

    // Parse the content as JSON
    const data = JSON.parse(content);

    // Save the data to output.json
    fs.writeFileSync('output.json', JSON.stringify(data, null, 2));
    console.log('Data saved to output.json');

    await browser.close();
  } catch (error) {
    console.error('Error:', error);
  }
})();
