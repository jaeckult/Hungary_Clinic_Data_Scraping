import * as cheerio from "cheerio";
import puppeteerExtra from "puppeteer-extra";
import stealthPlugin from "puppeteer-extra-plugin-stealth";
import { createObjectCsvWriter } from "csv-writer";
import axios from "axios";
import * as https from "https";
import fs from "fs";


puppeteerExtra.use(stealthPlugin());


const cities = ["Budapest", "Debrecen", "Szeged", "Miskolc", "Pécs", "Győr"];

const csvWriter = createObjectCsvWriter({
  path: "Hungary_Dentists.csv",
  header: [
    { id: "index", title: "Index" },
    { id: "clinicName", title: "Clinic Name" },
    { id: "dentistName", title: "Dentist Name" },
    { id: "address", title: "Address" },
    { id: "phone", title: "Phone" },
    { id: "email", title: "Email" },
    { id: "website", title: "Website" },
    { id: "googleUrl", title: "Google Maps URL" },
  ],
});

async function scrapeWebsiteForEmail(url) {
  if (!url) return null;

  try {
    const agent = new https.Agent({ rejectUnauthorized: false });
    const response = await axios.get(url, { httpsAgent: agent, timeout: 10000 });
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}/gi;
    const matches = response.data.match(emailRegex);
    return matches ? matches.find(email => !email.includes('example.com')) || null : null;
  } catch (error) {
    console.warn(`⚠️ Failed to fetch email from ${url}: ${error.message}`);
    return null;
  }
}

// Scrolls the Google Maps listings panel
async function autoScroll(page) {
  console.log("⏬ Scrolling page...");

  const feedExists = await page.$('div[role="feed"]');
  if (!feedExists) throw new Error("Google Maps feed panel not found.");

  await page.evaluate(async () => {
    const wrapper = document.querySelector('div[role="feed"]');
    if (!wrapper) return;

    await new Promise((resolve) => {
      let totalHeight = 0;
      const distance = 1000;
      const scrollDelay = 2000;

      const timer = setInterval(async () => {
        const scrollHeightBefore = wrapper.scrollHeight;
        wrapper.scrollBy(0, distance);
        totalHeight += distance;

        if (totalHeight >= scrollHeightBefore) {
          totalHeight = 0;
          await new Promise((res) => setTimeout(res, scrollDelay));
          const scrollHeightAfter = wrapper.scrollHeight;

          if (scrollHeightAfter <= scrollHeightBefore) {
            clearInterval(timer);
            resolve();
          }
        }
      }, 700);
    });
  });
}

// Main scraping logic
async function scrapeDentists() {
  const browser = await puppeteerExtra.launch({
    headless: "new",
    protocolTimeout: 180000,
    timeout: 180000,
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  const results = [];
  let index = 1;

  for (const city of cities) {
    let attempt = 0;
    let citySuccess = false;

    while (attempt < 2 && !citySuccess) {
      let page;
      try {
        attempt++;
        console.log(`\n🔍 Scraping city: ${city} (Attempt ${attempt})`);

        const query = `dentist in ${city}, Hungary`;
        page = await browser.newPage();

        console.log("🌐 Loading Google Maps...");
        await page.goto(`https://www.google.com/maps/search/${query.split(" ").join("+")}`, {
          waitUntil: "domcontentloaded",
          timeout: 60000,
        });

        await Promise.race([
          autoScroll(page),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error("Scroll timeout")), 90000)
          ),
        ]);

        console.log(`Done scrolling in ${city}`);

        const html = await page.content();
        const $ = cheerio.load(html);
        const aTags = $("a");
        const parents = [];

        aTags.each((_, el) => {
          const href = $(el).attr("href");
          if (href && href.includes("/maps/place/")) {
            parents.push($(el).parent());
          }
        });

        console.log(`Found ${parents.length} listings in ${city}`);

        for (const parent of parents) {
          const url = parent.find("a").attr("href");
          const website = parent.find('a[data-value="Website"]').attr("href") || "";
          const clinicName = parent.find("div.fontHeadlineSmall").text().trim();

          const bodyDiv = parent.find("div.fontBodyMedium").first();
          const children = bodyDiv.children();
          const lastChild = children.last();
          const firstOfLast = lastChild.children().first();
          const lastOfLast = lastChild.children().last();

          const address = firstOfLast?.text()?.split("·")?.[1]?.trim() || "";
          const phone = lastOfLast?.text()?.split("·")?.[1]?.trim() || "";
          const email = website ? await scrapeWebsiteForEmail(website) : "";

          console.log(`📝 (${index}) ${clinicName} - ${email || "no email"}`);

          results.push({
            index: index++,
            clinicName,
            dentistName: "",
            address,
            phone,
            email,
            website,
            googleUrl: url,
          });

          if (results.length >= 500) {
            console.log("Reached 500 records.");
            break;
          }
        }

        citySuccess = true;
      } catch (err) {
        console.warn(`Scraping failed in ${city} (Attempt ${attempt}): ${err.message}`);
        if (attempt >= 2) console.error(`Skipping ${city} after 2 failed attempts.`);
      } finally {
        if (page) {
          try {
            await page.close();
          } catch (_) {}
        }
      }

      if (results.length >= 500) break;
    }

    if (results.length >= 500) break;
  }

  await browser.close();
  return results;
}

// Entry point
(async function () {
  try {
    const data = await scrapeDentists();

    console.log("💾 Writing CSV...");
    await csvWriter.writeRecords(data);
    console.log("\nData successfully saved to Hungary_Dentists.csv");

    process.exit(0);
  } catch (error) {
    console.error("Scraping failed:", error.message);
    process.exit(1);
  }
})();
