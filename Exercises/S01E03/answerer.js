const fs = require('fs');
const path = require('path');
const https = require('https');
const fetch = require('node-fetch');
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

const dataPath = path.join(__dirname, 'data.json');
const data = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
const testData = data['test-data'];

async function getOpenAIAnswer(q) {
    const apiKey = process.env.OPENAI_API_KEY;
    const res = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
            model: 'gpt-3.5-turbo',
            messages: [
                { role: 'system', content: 'Answer concisely and factually. Do not include any explanation or commentary. Just streight to the point answer.' },
                { role: 'user', content: q }
            ],
            max_tokens: 32
        })
    });
    const out = await res.json();
    return out.choices[0].message.content.trim();
}

(async () => {
    for (const entry of testData) {
        if (typeof entry.question === 'string') {
            const m = entry.question.match(/^(\d+) \+ (\d+)$/);
            if (m) {
                const correct = parseInt(m[1], 10) + parseInt(m[2], 10);
                if (entry.answer !== correct) entry.answer = correct;
            } else if (typeof entry.answer !== 'string') {
                entry.answer = await getOpenAIAnswer(entry.question);
            }
        }
        if (entry.test && entry.test.q && entry.test.a === '???') {
            entry.test.a = await getOpenAIAnswer(entry.test.q);
            
        }
    }
    console.log("nice", testData.length);

    const payload = {
        task: 'JSON',
        apikey: process.env.DV_API_KEY,
        answer: {
            apikey: process.env.DV_API_KEY,
            description: data.description,
            copyright: data.copyright,
            'test-data': testData
        }
    };

    const postData = JSON.stringify(payload);
    const options = {
        hostname: 'c3ntrala.ag3nts.org',
        path: '/report',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData)
        }
    };
    const req = https.request(options, res => {
        let body = '';
        res.on('data', chunk => { body += chunk; });
        res.on('end', () => { console.log('Response:', body); });
    });
    req.on('error', e => { console.error('Request error:', e); });
    req.write(postData);
    req.end();
})();
