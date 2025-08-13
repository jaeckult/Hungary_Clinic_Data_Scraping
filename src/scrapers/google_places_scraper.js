// places-dentists-holland-scrape.mjs
import 'dotenv/config';
import * as cheerio from 'cheerio';
import pRetry from 'p-retry';
import pMap from 'p-map';
import fs from 'fs/promises';

const API_KEY = process.env.GOOGLE_API_KEY;
if (!API_KEY) throw new Error('Set GOOGLE_API_KEY in .env');

const TEXT_SEARCH_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json';
const DETAILS_URL = 'https://maps.googleapis.com/maps/api/place/details/json';

// Major cities in the Netherlands (Holland)
const LOCATIONS = [
  { name: 'Amsterdam', q: '52.3676,4.9041' },
  { name: 'Rotterdam', q: '51.9244,4.4777' },
  { name: 'The Hague', q: '52.0705,4.3007' },
  { name: 'Utrecht', q: '52.0907,5.1214' },
  { name: 'Eindhoven', q: '51.4416,5.4697' },
  { name: 'Tilburg', q: '51.5555,5.0913' },
  { name: 'Groningen', q: '53.2194,6.5665' },
  { name: 'Almere', q: '52.3508,5.2647' },
  { name: 'Breda', q: '51.5719,4.7683' },
  { name: 'Nijmegen', q: '51.8126,5.8372' },
  { name: 'Enschede', q: '52.2215,6.8937' },
  { name: 'Apeldoorn', q: '52.2112,5.9699' },
  { name: 'Haarlem', q: '52.3874,4.6462' },
  { name: 'Arnhem', q: '51.9851,5.8987' },
  { name: 'Amersfoort', q: '52.1561,5.3878' },
];

const queryText = 'Dentist'; // could also be 'Tandarts' for Dutch results

async function textSearch({ location, pagetoken }) {
  const params = new URLSearchParams({
    query: queryText,
    key: API_KEY
  });
  if (location) params.set('location', location);
  if (pagetoken) params.set('pagetoken', pagetoken);
  const url = `${TEXT_SEARCH_URL}?${params.toString()}`;
  const res = await fetch(url);
  const json = await res.json();
  if (json.status === 'REQUEST_DENIED') {
    throw new Error('Google request denied: ' + JSON.stringify(json));
  }
  return json;
}

// the rest of your code (getPlaceDetails, extractEmailFromWebsite, main) stays the same


async function getPlaceDetails(place_id) {
  const params = new URLSearchParams({
    place_id,
    fields: 'name,formatted_address,formatted_phone_number,website',
    key: API_KEY
  });
  const url = `${DETAILS_URL}?${params.toString()}`;
  const res = await fetch(url);
  const json = await res.json();
  if (json.status !== 'OK') return null;
  return json.result;
}

async function extractEmailFromWebsite(url) {
  if (!url) return null;
  if (!/^https?:\/\//i.test(url)) url = 'http://' + url;
  try {
    const res = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; ReikiScraper/1.0)' },
      timeout: 10000
    });
    if (!res.ok) return null;
    const html = await res.text();
    const $ = cheerio.load(html);

    const mailto = $("a[href^='mailto:']").first().attr('href');
    if (mailto) {
      const em = decodeURIComponent(mailto.replace(/^mailto:/i, '').split('?')[0]);
      if (/[^\s@]+@[^\s@]+\.[^\s@]+/.test(em)) return em;
    }
    const emails = html.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g);
    if (emails && emails.length) return emails[0];
    return null;
  } catch {
    return null;
  }
}

async function main() {
  try {
    const records = new Map();

    for (const loc of LOCATIONS) {
      if (records.size >= 100) break;
      console.log(`Searching around ${loc.name}`);

      let page = await textSearch({ location: loc.q });
      if (page.results?.length) {
        for (const r of page.results) {
          if (!records.has(r.place_id)) {
            records.set(r.place_id, {
              place_id: r.place_id,
              name: r.name,
              address: r.formatted_address
            });
          }
        }
      }

      let token = page.next_page_token;
      for (let i = 0; i < 2 && token; i++) {
        await new Promise(res => setTimeout(res, 2100));
        try {
          const next = await textSearch({ pagetoken: token });
          if (next.results?.length) {
            for (const r of next.results) {
              if (!records.has(r.place_id)) {
                records.set(r.place_id, {
                  place_id: r.place_id,
                  name: r.name,
                  address: r.formatted_address
                });
              }
            }
          }
          token = next.next_page_token;
        } catch (err) {
          console.warn('Next page fetch error:', err.message);
          break;
        }
      }

      console.log('Collected so far:', records.size);
      await new Promise(res => setTimeout(res, 500));
    }

    console.log(`Total unique places found (before details): ${records.size}`);
    const placeIds = Array.from(records.keys()).slice(0, 100);

    console.log('Starting to fetch details for', placeIds.length, 'places...');
    const details = await pMap(placeIds, async (place_id, index) => {
      try {
        console.log(`Processing place ${index + 1}/${placeIds.length}: ${place_id}`);
        const basic = records.get(place_id) || { place_id };
        const placeDetails = await pRetry(() => getPlaceDetails(place_id), { retries: 2 });
        const website = placeDetails?.website ?? null;
        const phone = placeDetails?.formatted_phone_number ?? null;
        const email = await pRetry(() => extractEmailFromWebsite(website), {
          retries: 1
        });
        return {
          place_id,
          name: placeDetails?.name ?? basic.name ?? null,
          address: placeDetails?.formatted_address ?? basic.address ?? null,
          phone,
          website,
          email
        };
      } catch (error) {
        console.error(`Error processing place ${place_id}:`, error.message);
        return {
          place_id,
          name: basic.name ?? null,
          address: basic.address ?? null,
          phone: null,
          website: null,
          email: null
        };
      }
    }, { concurrency: 3 });

    await fs.writeFile('UK_Ireland_reiki_practitioners.json', JSON.stringify(details, null, 2));

    const csv = [
      ['place_id', 'name', 'address', 'phone', 'website', 'email'].join(',')
    ].concat(details.map(d => {
      return [
        `"${(d.place_id || '').replace(/"/g, '""')}"`,
        `"${(d.name || '').replace(/"/g, '""')}"`,
        `"${(d.address || '').replace(/"/g, '""')}"`,
        `"${(d.phone || '').replace(/"/g, '""')}"`,
        `"${(d.website || '').replace(/"/g, '""')}"`,
        `"${(d.email || '').replace(/"/g, '""')}"`,
      ].join(',');
    })).join('\n');

    await fs.writeFile('UK_Ireland_reiki_practitioners.csv', csv);
    console.log('Done. Files: UK_Ireland_reiki_practitioners.json, UK_Ireland_reiki_practitioners.csv');
  } catch (err) {
    console.error('Fatal error:', err);
  }
}

main();
