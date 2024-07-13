import axios, { AxiosResponse} from 'axios';
import * as dotenv from 'dotenv';

dotenv.config();

// const API_URL = 'https://api.openai.com/v1/engines/davinci-codex/completions';
// const apiUrl = ''
const apiKey = process.env.CHATGPT_API_KEY;

class chatGptClient {
    private static instance: chatGptClient;
    private baseURL: string;
    private headers: object;

    private constructor() {
        this.baseURL = 'https://api.openai.com/v1';
        this.headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${process.env.CHATGPT_API_KEY}`,
        };
    }

    public static getInstance(): chatGptClient {
        if (!chatGptClient.instance) {
            chatGptClient.instance = new chatGptClient();
        }
        return chatGptClient.instance;
    }
¥
    public async generateChat(prompt: string, maxTokens: number = 300): Promise<{consumedTokens: number, reply: string}> {
        // https://platform.openai.com/docs/api-reference/chat/create
        // Model endpoint compatibility: https://platform.openai.com/docs/models/model-endpoint-compatibility
        const data = {
            'model': 'gpt-3.5-turbo',
            messages: [
                {
                    role: "system",
                    content: "You are a professional for science, technology, and humanities."
                },
                {
                'role': 'user',
                'content': prompt,
                // 'name': 'SomeOne',
                }
            ],
            max_tokens: maxTokens,
            temperature: 0.8,
            n: 1,
        };

        try {
            const response: AxiosResponse = await axios.post(
                `${this.baseURL}/chat/completions`,
                data,
                { headers: this.headers },
            );
            return {consumedTokens: response.data.usage.total_tokens, reply: response.data.choices[0].message.content};
        } catch (e) {
            // throw new Error(e);
            console.error(e);
            throw new Error("chatGptClient.generateChat() failed.....");
            
        }
    }
}

export default chatGptClient
