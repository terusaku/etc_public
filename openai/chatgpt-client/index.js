"use strict";
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
const gptClient_1 = __importDefault(require("./gptClient"));
// import readline from 'readline';
// const rl = readline.createInterface({
//     input: process.stdin,
//     output: process.stdout,
// });
function callChatGpt(text) {
    return __awaiter(this, void 0, void 0, function* () {
        const chatClient = gptClient_1.default.getInstance();
        const resp = yield chatClient.generateChat(text);
        console.log(`合計トークン: ${resp.consumedTokens}`, '\n', '回答: ', resp.reply);
    });
}
function run() {
    return __awaiter(this, void 0, void 0, function* () {
        const args = process.argv.slice(2);
        console.log(args);
        if (args.length > 0) {
            const prompt = args.join(' ');
            callChatGpt(prompt);
        }
        else {
            const prompt = 'こんにちは、何を得手としていますか？' + '\n';
            callChatGpt(prompt);
        }
    });
}
// run().catch(console.error);
run();
