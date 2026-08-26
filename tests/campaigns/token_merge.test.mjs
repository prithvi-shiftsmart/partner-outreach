import fs from 'fs';
// Extracts the real TOKEN_RESOLVERS / mergeTemplate / friendlyCompany from
// campaigns.js and exercises them. Run:  node tests/campaigns/token_merge.test.mjs
import path from 'path';
import { fileURLToPath } from 'url';
const __dir = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dir, '../..');
const SRC = path.join(ROOT, 'frontend/js/tabs/campaigns.js');
const _src = fs.readFileSync(SRC, 'utf8');
const _grab = (a, b) => { const i = _src.indexOf(a); return _src.slice(i, _src.indexOf(b, i)); };
const _fcI = _src.indexOf('function friendlyCompany');
const _extracted = _grab('const TOKEN_RESOLVERS', 'function availableTokens')
  + _src.slice(_fcI, _src.indexOf('\n}\n', _fcI) + 3)
  + '\nexport { mergeTemplate, friendlyCompany };\n';
const _tmp = path.join(ROOT, 'tests/campaigns/.merge_extracted.mjs');
fs.writeFileSync(_tmp, _extracted);
const { mergeTemplate } = await import(_tmp);
fs.unlinkSync(_tmp);
const rows = fs.readFileSync(path.join(__dir, 'fixtures/tuesday_confirm.csv'), 'utf8');
// minimal CSV parse (quoted, embedded newlines)
function parseCSV(t){const out=[];let f='',row=[],q=false;for(let i=0;i<t.length;i++){const c=t[i];
 if(q){ if(c==='"'){ if(t[i+1]==='"'){f+='"';i++;} else q=false;} else f+=c; }
 else { if(c==='"')q=true; else if(c===','){row.push(f);f='';} else if(c==='\n'){row.push(f);out.push(row);row=[];f='';} else if(c!=='\r')f+=c; } }
 if(f||row.length){row.push(f);out.push(row);} const h=out.shift();
 return out.filter(r=>r.length===h.length).map(r=>Object.fromEntries(h.map((k,i)=>[k,r[i]])));}
const data = parseCSV(rows);

let pass=0, fail=0;
const t=(name,cond)=>{ cond?pass++:fail++; console.log((cond?'PASS':'FAIL')+'  '+name); };

// 1. the real template reproduces the query's rendered message
for (const r of data) {
  const {msg, unknown} = mergeTemplate('Hi {first_name}! {market}', r);
  t(`merge matches query message — ${r.first_name}`, msg === r.message);
  t(`no unknown tokens — ${r.first_name}`, unknown.length === 0);
}
// 2. arbitrary columns now work (this is the whole point)
const r0 = data[0];
t('arbitrary column {store_numbers} merges', mergeTemplate('x {store_numbers} y', r0).msg === `x ${r0.store_numbers} y`);
t('arbitrary column {zone_description} merges', mergeTemplate('{zone_description}', r0).msg === r0.zone_description);
t('{message} now merges instead of sending literally', mergeTemplate('{message}', r0).msg === r0.message);
// 3. unknown tokens are preserved and reported, never blanked
const u = mergeTemplate('Hi {first_name}, {nope} {alsonope}', r0);
t('unknown token left literal', u.msg.includes('{nope}') && u.msg.includes('{alsonope}'));
t('unknown tokens reported', u.unknown.join(',') === 'nope,alsonope');
// 4. present-but-empty column renders empty and does NOT warn
const e = mergeTemplate('[{company}]', r0);
t('empty column -> empty string, no warning', e.msg === '[]' && e.unknown.length === 0);
// 5. special resolvers still work
t('company_name friendly mapping', mergeTemplate('{company_name}', {company_name:'Circle K - Premium'}).msg === 'Circle K');
t('phone falls back to phone_number', mergeTemplate('{phone}', {phone_number:'+15551234'}).msg === '+15551234');
// 6. non-token braces untouched
t('non-token braces untouched', mergeTemplate('a {not a token} b', r0).msg === 'a {not a token} b');
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail?1:0);
