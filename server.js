require('dotenv').config();
const http = require('http');
const { GoogleGenerativeAI } = require('google-generative-ai');

const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);

const DEFAULT_PROMPT = "Summarize the following text concisely:";

const server = http.createServer(async (req, res) => {
    if (req.method === 'POST' && req.url === '/summarize') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });

        req.on('end', async () => {
            try {
                const { user_prompt, prompt, model } = JSON.parse(body);
                const finalPrompt = `${prompt || DEFAULT_PROMPT}\n${user_prompt}`;
                const chosenModel = model || "gemini-pro";

                res.writeHead(200, { "Content-Type": "application/json" });

                const modelInstance = genAI.getGenerativeModel({ model: chosenModel });
                const result = await modelInstance.generateContentStream(finalPrompt);
                
                for await (const chunk of result.stream) {
                    res.write(JSON.stringify({ text: chunk.text || "" }));
                }
                res.end();
            } catch (error) {
                res.writeHead(500, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ error: error.message }));
            }
        });
    } else {
        res.writeHead(404, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Not Found" }));
    }
});

server.listen(3000, () => console.log('Server running on port 3000'));
