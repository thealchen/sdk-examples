const dotenv = require("dotenv");
const { wrapOpenAI, flush, init } = require("galileo");
const { OpenAI } = require("openai");

dotenv.config(); // Load environment variables

const openai = wrapOpenAI(new OpenAI({ apiKey: process.env.OPENAI_API_KEY }));

async function run() {
  init();

  const result = await openai.chat.completions.create({
    model: "gpt-4o",
    messages: [{ content: "Say hello world!", role: "user" }],
  });

  console.log(result.choices[0].message.content); // Access the response

  flush();
}

run().catch(console.error);