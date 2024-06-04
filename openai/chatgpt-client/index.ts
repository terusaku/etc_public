import chatGptClient from './gptClient';

// import readline from 'readline';
// const rl = readline.createInterface({
//     input: process.stdin,
//     output: process.stdout,
// });

async function callChatGpt(text: string) {
    const chatClient = chatGptClient.getInstance();
    const resp = await chatClient.generateChat(text);
    console.log(`合計トークン: ${resp.consumedTokens}`, '\n', '回答: ', resp.reply);
}

async function run() {
    const args = process.argv.slice(2);
    console.log(args);

    if (args.length > 0) {
        const prompt = args.join(' ');
        callChatGpt(prompt);
    } else {
        const prompt = 'こんにちは、自己紹介と何を得手としているのか教えてください' + '\n';
        callChatGpt(prompt);
    }

}

// run().catch(console.error);
run();
