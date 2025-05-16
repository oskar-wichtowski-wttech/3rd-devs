import puppeteer from 'puppeteer';
import OpenAI from 'openai';
import dotenv from 'dotenv';

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

async function getAnswerFromLLM(question: string): Promise<number> {
  const prompt = `Answer the following question with a number or date only, no explanation: ${question}`;
  
  const completion = await openai.chat.completions.create({
    messages: [{ role: "user", content: prompt }],
    model: "gpt-3.5-turbo",
  });

  const answer = completion.choices[0].message.content;
  return parseInt(answer || "0", 10);
}

async function main() {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();

  try {
    await page.goto('https://xyz.ag3nts.org/');
    
    const question = await page.$eval('#human-question', el => el.textContent);
    if (!question) {
      throw new Error('Question not found');
    }

    console.log('Question:', question);
    const answer = await getAnswerFromLLM(question);
    console.log('Answer:', answer);

    await page.type('input[name="username"]', 'tester');
    await page.type('input[name="password"]', '574e112a');
    await page.type('input[name="answer"]', answer.toString());

    await page.click('button[type="submit"]');
    
    await page.waitForNavigation();
    
    console.log('Form submitted successfully');
  } catch (error) {
    console.error('Error:', error);
  }
}

main();