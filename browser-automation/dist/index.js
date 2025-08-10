#!/usr/bin/env node
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { program } from 'commander';
import path from 'path';
import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
class BrowserAutomationCLI {
    client = null;
    transport = null;
    async connectToMCP() {
        console.log('Playwright MCPサーバーに接続中...');
        try {
            this.client = new Client({
                name: "browser-automation-cli",
                version: "1.0.0"
            }, {
                capabilities: {}
            });
            const transportOptions = {
                command: 'npx',
                args: ['@playwright/mcp@latest']
            };
            console.log('npx経由でPlaywright MCPサーバーを起動します...');
            this.transport = new StdioClientTransport(transportOptions);
            await this.client.connect(this.transport);
            console.log('✅ Playwright MCPサーバーに正常に接続しました');
            return this.transport;
        }
        catch (error) {
            console.error('❌ MCPサーバーへの接続に失敗:', error);
            console.error('💡 トラブルシューティング:');
            console.error('   1. npx @playwright/mcp が動作するか確認してください');
            console.error('   2. npx playwright install でブラウザをインストール');
            console.error('   3. ネットワーク接続を確認');
            console.error('   4. 手動テスト: npx @playwright/mcp');
            throw error;
        }
    }
    async executeAction(url, action) {
        console.log(`\n🌐 URL: ${url}`);
        console.log(`🤖 操作: ${action}\n`);
        try {
            console.log('ブラウザを起動中...');
            await this.callMCPTool('browser_navigate', { url });
            let shotCount = 1;
            console.log('現在のページをスクリーンショット中...');
            await this.callMCPTool('browser_take_screenshot', {
                filename: `/Users/31012015-AMA/Downloads/browser_snapshot${shotCount}.png`
            });
            shotCount++;
            console.log('操作を実行中...');
            const result = await this.callMCPTool('browser_click', {
                text: action
            });
            console.log(`✅ ${action}操作が正常に完了しました`);
            console.log('結果:', result.content[0]?.text || '操作完了');
            console.log('現在のページをスクリーンショット中...');
            await this.callMCPTool('browser_take_screenshot', {
                filename: `/Users/31012015-AMA/Downloads/browser_snapshot${shotCount}.png`
            });
            shotCount++;
        }
        catch (error) {
            console.error('❌ 操作の実行中にエラーが発生:', error);
            throw error;
        }
    }
    async callMCPTool(toolName, args) {
        if (!this.client) {
            throw new Error('MCPクライアントが初期化されていません');
        }
        try {
            const response = await this.client.callTool({
                name: toolName,
                arguments: args
            });
            return response;
        }
        catch (error) {
            console.error(`❌ ツール ${toolName} の呼び出しに失敗:`, error);
            throw error;
        }
    }
    async close() {
        if (this.client) {
            await this.client.close();
        }
        if (this.transport) {
            await this.transport.close();
        }
    }
}
program
    .name('browser-automation')
    .description('自然言語でブラウザ操作を行うCLIツール')
    .version('1.0.0')
    .argument('<url>', 'アクセスするURL')
    .argument('<action>', '実行する操作の内容（自然言語）')
    .option('-v, --verbose', '詳細なログを表示')
    .action(async (url, action, options) => {
    const cli = new BrowserAutomationCLI();
    try {
        await cli.connectToMCP();
        await cli.executeAction(url, action);
    }
    catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error('❌ アプリケーションの実行中にエラーが発生:', errorMessage);
        if (errorMessage.includes('ENOENT') || errorMessage.includes('not found')) {
            console.error('💡 解決方法: npm install -g @playwright/mcp を実行してください');
        }
        process.exit(1);
    }
    finally {
        await cli.close();
        console.log('\n🔄 アプリケーションを終了しました');
    }
});
program.addHelpText('after', `

使用例:
  $ browser-automation "https://example.com" "検索ボックスに'Hello World'と入力して検索ボタンをクリック"
  $ browser-automation "https://github.com" "ログインボタンをクリックしてユーザー名欄に'myuser'と入力"
  $ browser-automation "https://shopping.com" "商品一覧から最初の商品をクリックしてカートに追加"

注意:
  - 事前にPlaywright MCPサーバーが利用可能である必要があります
  - 複雑な操作は段階的に分けて実行することを推奨します
`);
program.parse();
//# sourceMappingURL=index.js.map