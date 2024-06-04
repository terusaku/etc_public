"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const axios_1 = __importDefault(require("axios"));
const dotenv = __importStar(require("dotenv"));
dotenv.config();
// const API_URL = 'https://api.openai.com/v1/engines/davinci-codex/completions';
// const apiUrl = ''
const apiKey = process.env.CHATGPT_API_KEY;
class chatGptClient {
    constructor() {
        this.baseURL = 'https://api.openai.com/v1';
        this.headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${process.env.CHATGPT_API_KEY}`,
        };
    }
    static getInstance() {
        if (!chatGptClient.instance) {
            chatGptClient.instance = new chatGptClient();
        }
        return chatGptClient.instance;
    }
    generateChat(prompt, maxTokens = 300) {
        return __awaiter(this, void 0, void 0, function* () {
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
                const response = yield axios_1.default.post(`${this.baseURL}/chat/completions`, data, { headers: this.headers });
                return { consumedTokens: response.data.usage.total_tokens, reply: response.data.choices[0].message.content };
            }
            catch (e) {
                // throw new Error(e);
                console.error(e);
                throw new Error("chatGptClient.generateChat() failed.....");
            }
        });
    }
}
exports.default = chatGptClient;
