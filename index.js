import * as cheerio from "cheerio";
import puppeteerExtra from "puppeteer-extra";
import stealthPlugin from "puppeteer-extra-plugin-stealth";
import { createObjectCsvWriter } from "csv-writer";

puppeteerExtra.use(stealthPlugin());

const countries = ["England", "Ireland", "Scotland", "Wales"];

const csvWriter = createObjectCsvWriter({
  path: "UK_Reiki_Prakts.csv",
  header: [
    { id: "index", title: "Index" },
    { id: "practitionerName", title: "Practitioner Name" },
    { id: "address", title: "Address" },
    { id: "phone", title: "Phone" },
    { id: "email", title: "Email" },
    { id: "website", title: "Website" },
    { id: "googleUrl", title: "Google Maps URL" },
  ],
});

async function scrapeWebsiteForEmail(url, browser) {
  console.log(`🌐 Trying to extract email from: ${url}`);
  if (!url) return null;

  const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}/gi;
  const possiblePaths = ["", "/contact", "/contact-us", "/about", "/about-us"];
  let email = null;

  const page = await browser.newPage();
  try {
    for (const path of possiblePaths) {
      const targetUrl = path ? `${url.replace(/\/$/, "")}${path}` : url;
      console.log(`📡 Navigating to: ${targetUrl}`);
      await page.goto(targetUrl, { waitUntil: "networkidle2", timeout: 15000 });

      // Check for mailto links
      const mailtoLinks = await page.$$eval('a[href^="mailto:"]', links =>
        links.map(link => link.href.replace("mailto:", "").trim()));
      if (mailtoLinks.length) {
        email = mailtoLinks.find(e => emailRegex.test(e));
        if (email) {
          console.log(`📧 Email found in mailto: ${email}`);
          return email;
        }
      }

      // Check page content for emails
      const content = await page.content();
      const matches = content.match(emailRegex);
      if (matches) {
        email = matches.find(e => !e.includes("example.com") && !e.includes("w3.org")) || null;
        if (email) {
          console.log(`📧 Email found in text: ${email}`);
          return email;
        }
      }
    }
    console.warn(`⚠️ No valid email found on ${url}`);
    return null;
  } catch (error) {
    console.warn(`⚠️ Failed to fetch email from ${url}: ${error.message}`);
    return null;
  } finally {
    await page.close();
  }
}

async function autoScroll(page) {
  console.log("⏬ Scrolling the listings on the Google Maps results page...");
  const feedExists = await page.$('div[role="feed"]');
  if (!feedExists) throw new Error("Google Maps feed panel not found.");

  await page.evaluate(async () => {
    const wrapper = document.querySelector('div[role="feed"]');
    if (!wrapper) return;

    await new Promise((resolve) => {
      let totalHeight = 0;
      const distance = 2000;
      const scrollDelay = 3000;

      const timer = setInterval(async () => {
        const scrollHeightBefore = wrapper.scrollHeight;
        wrapper.scrollBy(0, distance);
        totalHeight += distance;
        console.log("🌀 Scrolling...");

        if (totalHeight >= scrollHeightBefore) {
          totalHeight = 0;
          await new Promise((res) => setTimeout(res, scrollDelay));
          const scrollHeightAfter = wrapper.scrollHeight;

          if (scrollHeightAfter <= scrollHeightBefore) {
            console.log("📦 Done scrolling listings.");
            clearInterval(timer);
            resolve();
          }
        }
      }, 1000);
    });
  });
}

async function scrapeListingDetails(page, googleUrl) {
  let website = "";
  try {
    console.log(`🔍 Navigating to listing details: ${googleUrl}`);
    await page.goto(googleUrl, { waitUntil: "networkidle2", timeout: 30000 });
    const content = await page.content();
    const $ = cheerio.load(content);

    // Try multiple selectors for website
    const websiteLink = $('a[href*="http"]:not([href*="google.com"])');
    if (websiteLink.length) {
      website = websiteLink.attr("href") || "";
      console.log(`🔗 Found website link: ${website}`);
    } else {
      console.log(`🔍 No website link found in details page, checking text...`);
      const potentialWebsite = $('div').filter((_, el) => {
        const text = $(el).text().trim();
        return text.match(/^(https?:\/\/)?([\w-]+\.)+[\w-]{2,}(\/.*)?$/i);
      }).first().text().trim();
      website = potentialWebsite ? (potentialWebsite.startsWith('http') ? potentialWebsite : `https://${potentialWebsite}`) : "";
      console.log(`🔍 Potential website text: ${website || "None"}`);
    }

    // Validate website
    const urlRegex = /^(https?:\/\/)?([\w-]+\.)+[\w-]{2,}(\/.*)?$/i;
    if (website && !urlRegex.test(website)) {
      console.warn(`⚠️ Invalid website URL: ${website}`);
      website = "";
    }

    return website;
  } catch (error) {
    console.warn(`⚠️ Failed to scrape details page ${googleUrl}: ${error.message}`);
    return "";
  }
}

async function scrapeReikiPractitioners() {
  console.log("🚀 Launching Puppeteer browser...");
  const browser = await puppeteerExtra.launch({
    headless: "new",
    protocolTimeout: 180000,
    timeout: 180000,
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  const results = [];
  let index = 1;

  const concurrencyLimit = 2;
  const countryPromises = countries.map((country) => async () => {
    let attempt = 0;
    let countrySuccess = false;
    let page;

    while (attempt < 2 && !countrySuccess && results.length < 100) {
      try {
        attempt++;
        console.log(`🔍 Searching for Reiki practitioners in ${country} (Attempt ${attempt})`);
        page = await browser.newPage();
        const query = `Reiki practitioner in ${country}`;
        const searchUrl = `https://www.google.com/maps/search/${query.split(" ").join("+")}`;
        console.log(`🌍 Navigating to: ${searchUrl}`);
        await page.goto(searchUrl, {
          waitUntil: "domcontentloaded",
          timeout: 60000,
        });

        await Promise.race([
          autoScroll(page),
          new Promise((_, reject) => setTimeout(() => reject(new Error("Scroll timeout")), 90000)),
        ]);

        console.log("📄 Extracting HTML content...");
        const html = await page.content();
        const $ = cheerio.load(html);
        const aTags = $("a");
        const parents = [];

        console.log("🔎 Locating map listing URLs...");
        aTags.each((_, el) => {
          const href = $(el).attr("href");
          if (href && href.includes("/maps/place/")) {
            parents.push($(el).parent());
          }
        });

        console.log(`📌 Found ${parents.length} listing containers.`);

        for (const parent of parents) {
          console.log("📥 Extracting info from a listing...");
          const googleUrl = parent.find("a").attr("href") || "";
          const practitionerName = parent.find("div.fontHeadlineSmall").text().trim();
          const bodyDiv = parent.find("div.fontBodyMedium").first();
          const children = bodyDiv.children();
          const lastChild = children.last();
          const firstOfLast = lastChild.children().first();
          const lastOfLast = lastChild.children().last();
          const address = firstOfLast?.text()?.split("·")?.[1]?.trim() || "";
          const phone = lastOfLast?.text()?.split("·")?.[1]?.trim() || "";

          // Try to find website in main listing
          let website = "";
          const websiteLink = parent.find('a[href*="http"]:not([href*="google.com"])');
          if (websiteLink.length) {
            website = websiteLink.attr("href") || "";
            console.log(`🔗 Found website in main listing: ${website}`);
          } else {
            console.log(`🔍 No website in main listing for ${practitionerName}, checking details page...`);
            website = await scrapeListingDetails(page, googleUrl);
          }

          const email = website ? await scrapeWebsiteForEmail(website, browser) : "";

          console.log(`✅ Collected: ${practitionerName || "Unnamed"} | ${address} | ${phone} | ${email || "No email"} | ${website || "No website"}`);

          results.push({
            index: index++,
            practitionerName,
            address,
            phone,
            email,
            website,
            googleUrl,
          });

          await new Promise(resolve => setTimeout(resolve, 1000));

          if (results.length >= 100) break;
        }

        countrySuccess = true;
      } catch (err) {
        console.warn(`⚠️ Error in ${country} (Attempt ${attempt}): ${err.message}`);
      } finally {
        if (page) await page.close();
      }
    }
  });

  await Promise.all(countryPromises.map(async (task, i) => {
    if (i % concurrencyLimit === 0) await task();
    else await new Promise(resolve => setTimeout(resolve, i * 1000)).then(task);
  }));

  console.log("🧹 Closing browser...");
  await browser.close();
  return results;
}

(async function () {
  try {
    console.log("🎬 Starting scrape process...");
    const data = await scrapeReikiPractitioners();

    console.log("💾 Writing data to CSV...");
    await csvWriter.writeRecords(data);
    console.log("✅ Successfully saved data to UK_Reiki_Prakts.csv");

    process.exit(0);
  } catch (error) {
    console.error("❌ Scraping failed:", error.message);
    process.exit(1);
  }
})();